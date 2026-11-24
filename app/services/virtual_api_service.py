"""Virtual APIs: a saved (prompt + model + schema) that becomes a one-call HTTP endpoint."""
import json
from typing import AsyncIterator

from ..core.errors import AppError
from ..db.repositories import VirtualApiRepo
from ..schemas import PresetOptions, VirtualRun
from .completion import CompletionService
from .model_manager import ModelManager
from .prompting import append_to_last_user, render_template


class VirtualApiService:
    def __init__(self, repo: VirtualApiRepo, manager: ModelManager, completion: CompletionService):
        self.repo, self.manager, self.completion = repo, manager, completion

    async def _prepare(self, slug: str, run: VirtualRun):
        api = await self.repo.get(slug)
        if not api:
            raise AppError(404, "virtual_api_not_found", f"No virtual API named '{slug}'.")
        await self.manager.ensure(api["model_filename"], api["preset_id"])
        if self.manager.current is None:
            raise AppError(409, "no_model_loaded", "No model is loaded. Load one from the Models page first.")
        text = render_template(api["input_template"], run.input, run.variables)
        messages = ([{"role": "system", "content": api["system_prompt"]}] if api["system_prompt"].strip() else [])
        messages.append({"role": "user", "content": text})
        options = PresetOptions.model_validate(self.manager.current.options)
        if not run.thinking:
            append_to_last_user(messages, options.think_off_directive)
        params = self.completion.build_params(run.gen, api["output_schema"], api["gen_params"])
        return api, messages, params, options.think_prefilled

    async def run(self, slug: str, run: VirtualRun) -> dict:
        api, messages, params, prefilled = await self._prepare(slug, run)
        result = await self.completion.collect(messages, params, prefilled=prefilled)
        body = {"output": result["content"], "model": self.manager.current.filename,
                "usage": {"completion_tokens": result["completion_tokens"], "seconds": result["seconds"]}}
        if run.thinking and result["reasoning"]:
            body["reasoning"] = result["reasoning"]
        if api["output_schema"]:
            try:
                body["output"] = json.loads(result["content"])
            except json.JSONDecodeError as exc:
                raise AppError(502, "invalid_model_output", "The model did not return valid JSON.",
                               {"raw": result["content"]}) from exc
        return body

    async def stream(self, slug: str, run: VirtualRun) -> tuple[AsyncIterator[tuple[str, object]], bool]:
        _, messages, params, prefilled = await self._prepare(slug, run)
        return self.completion.stream(messages, params, prefilled=prefilled), run.thinking
