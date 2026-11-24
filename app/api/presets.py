import sqlite3

from fastapi import APIRouter, Depends

from ..container import Container
from ..core.errors import AppError
from ..schemas import PresetIn
from .deps import get_container

router = APIRouter(prefix="/presets", tags=["presets"])


@router.get("")
async def list_presets(c: Container = Depends(get_container)):
    return await c.presets.list()


@router.post("", status_code=201)
async def create_preset(body: PresetIn, c: Container = Depends(get_container)):
    try:
        return await c.presets.create(body.name, body.model_filename, body.load_params, body.gen_params, body.options)
    except sqlite3.IntegrityError:
        raise AppError(409, "preset_exists", f"A preset named '{body.name}' already exists.")


@router.put("/{preset_id}")
async def update_preset(preset_id: str, body: PresetIn, c: Container = Depends(get_container)):
    if not await c.presets.get(preset_id):
        raise AppError(404, "preset_not_found", "Preset not found.")
    try:
        return await c.presets.update(preset_id, body.name, body.model_filename, body.load_params,
                                      body.gen_params, body.options)
    except sqlite3.IntegrityError:
        raise AppError(409, "preset_exists", f"A preset named '{body.name}' already exists.")


@router.delete("/{preset_id}", status_code=204)
async def delete_preset(preset_id: str, c: Container = Depends(get_container)):
    await c.presets.delete(preset_id)
