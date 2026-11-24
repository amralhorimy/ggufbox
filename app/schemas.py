import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LoadParams(BaseModel):
    """Applied when the model is loaded into RAM. Changing any of these means a reload."""
    n_ctx: int = Field(4096, ge=256, le=1_048_576)
    n_gpu_layers: int = Field(0, ge=-1)
    n_threads: int | None = Field(None, ge=1, le=512)
    n_batch: int = Field(512, ge=1, le=16384)
    flash_attn: bool = False
    use_mmap: bool = True
    use_mlock: bool = False
    vision_handler: str | None = None
    chat_format: str | None = None


class GenSettings(BaseModel):
    """Sampling settings. Cheap to change on every request."""
    temperature: float = Field(0.7, ge=0, le=2)
    top_p: float = Field(0.95, gt=0, le=1)
    top_k: int = Field(40, ge=0)
    min_p: float = Field(0.05, ge=0, le=1)
    max_tokens: int = Field(1024, ge=1, le=131072)
    repeat_penalty: float = Field(1.1, ge=0.5, le=2)
    seed: int | None = None
    stop: list[str] | None = None


class PresetOptions(BaseModel):
    think_prefilled: bool = Field(False, description="The chat template already opens <think>, so output starts mid-thought.")
    think_off_directive: str = Field("", description='Text appended to the user turn when thinking is off, e.g. "/no_think".')


class PresetIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    model_filename: str | None = None
    load_params: dict[str, Any] = Field(default_factory=dict)
    gen_params: dict[str, Any] = Field(default_factory=dict)
    options: dict[str, Any] = Field(default_factory=dict)

    @field_validator("load_params")
    @classmethod
    def _load(cls, v):
        return LoadParams.model_validate(v).model_dump(exclude_unset=True)

    @field_validator("gen_params")
    @classmethod
    def _gen(cls, v):
        return GenSettings.model_validate(v).model_dump(exclude_unset=True)

    @field_validator("options")
    @classmethod
    def _opt(cls, v):
        return PresetOptions.model_validate(v).model_dump(exclude_unset=True)


class LoadRequest(BaseModel):
    filename: str
    preset_id: str | None = None
    overrides: dict[str, Any] = Field(default_factory=dict, description="Load params that win over the preset.")
    force: bool = Field(False, description="Load even if the RAM estimate says it will not fit.")


class ChatCreate(BaseModel):
    title: str | None = Field(None, max_length=120)
    system_prompt: str = ""


class ChatUpdate(BaseModel):
    title: str | None = Field(None, max_length=120)
    system_prompt: str | None = None


class SendMessage(BaseModel):
    content: str = ""
    attachments: list[str] = Field(default_factory=list)
    thinking: bool = False
    stream: bool = True
    regenerate: bool = Field(False, description="Re-answer the last user message instead of adding a new one.")
    gen: dict[str, Any] = Field(default_factory=dict, description="Per-request sampling overrides.")


_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,40}$")


class VirtualApiIn(BaseModel):
    slug: str
    name: str = Field(min_length=1, max_length=80)
    description: str = ""
    system_prompt: str = ""
    input_template: str = Field("", description="Use {{input}} and {{variable}} placeholders.")
    preset_id: str | None = None
    model_filename: str | None = Field(None, description="Pin a model; it is loaded on demand if needed.")
    gen_params: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] | None = Field(None, description="JSON Schema the output must follow.")

    @field_validator("slug")
    @classmethod
    def _slug_ok(cls, v):
        if not _SLUG.match(v):
            raise ValueError("slug must be 2-41 chars of a-z, 0-9 and '-'")
        return v

    @field_validator("gen_params")
    @classmethod
    def _gen(cls, v):
        return GenSettings.model_validate(v).model_dump(exclude_unset=True)


class VirtualRun(BaseModel):
    input: str = ""
    variables: dict[str, str] = Field(default_factory=dict)
    stream: bool = False
    thinking: bool = False
    gen: dict[str, Any] = Field(default_factory=dict)


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible request. Unknown fields are accepted and ignored."""
    model_config = ConfigDict(extra="allow")
    model: str | None = None
    messages: list[dict[str, Any]]
    stream: bool = False
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    seed: int | None = None
    stop: str | list[str] | None = None
    response_format: dict[str, Any] | None = None
