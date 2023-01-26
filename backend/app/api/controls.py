import base64
import io
import os
import uuid
from itertools import groupby

import PIL
import aiofiles.os
import blurhash
import math
from PIL import Image, ImageFont, ImageDraw
from fastapi import UploadFile, HTTPException
from starlette import status

from app import base_dir
from app.FakeUser import fUser, FakeUser
from app.crud.user import CRUDUser

IMAGE_DIR = "images"


def logic_check_depends(current_user, data_before_transformation):
    def mapped(elem):
        if elem == "current_user":
            return str(current_user.id)
        else:
            return data_before_transformation.get(elem, None)

    return mapped


def img_2_b64(image):
    buff = io.BytesIO()
    image.save(buff, format="JPEG")
    img_str = base64.b64encode(buff.getvalue()).decode("utf-8")
    return img_str


async def check_depends(depends, current_user, data_before_transformation):
    callback = logic_check_depends(current_user, data_before_transformation)
    models_depends = []

    if len(depends) == 0:
        return False

    for a_crud, meta in depends.items():
        a_dict = {}

        for key, value in meta.items():
            if isinstance(value, list):
                elems = list(map(callback, value))

                g = list(groupby(elems))

                if len(g) == 1 and g[0] is not None:
                    a_dict[key] = elems[0]
                else:
                    a_dict = {}
                    break
            else:
                elem = callback(value)
                if elem is not None:
                    a_dict[key] = elem

        if len(a_dict) > 0:
            raw_data = await a_crud.get(query=a_dict, mode="get_one")
            models_depends.append(raw_data is not None)
        else:
            models_depends.append(False)

    depends_bool = any(models_depends)

    return depends_bool


class Controls:
    def __init__(self, api):
        self.api = api

    @staticmethod
    async def create_image(cls, schema_in, file: UploadFile | None = None):
        if file is None:
            return False

        if len(file.filename.split(".")) == 0:
            return False

        extension = file.filename.split(".")[-1]
        new_name = str(uuid.uuid4())
        ratio = None

        if extension.lower() == "jpg":
            extension = "jpeg"

        if isinstance(schema_in, dict):
            ratio = schema_in.get("ratio", None)
        else:
            if hasattr(schema_in, "ratio"):
                ratio = schema_in.ratio

        file.filename = f"{new_name}.{extension}"
        contents = await file.read()

        io_bytes_file = io.BytesIO(contents)
        try:
            image = Image.open(io_bytes_file)
            image.verify()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Image is not valid.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        image = Image.open(io_bytes_file)

        title_font = ImageFont.truetype(
            os.path.join(base_dir, 'Roboto-Bold.ttf'),
            math.ceil(image.width * 0.8 / len(os.environ["IMAGE_TEXT"]))
        )
        title_text = os.environ["IMAGE_TEXT"]
        image_editable = ImageDraw.Draw(image)
        font_size = title_font.getsize(text=title_text)

        image_editable.text(
            (0, 0),
            title_text,
            (255, 255, 255),
            font=title_font
        )
        image_editable.text(
            (image.width - font_size[0], 0),
            title_text,
            (255, 255, 255),
            font=title_font
        )
        image_editable.text(
            (1 * image.width - font_size[0], 1 * image.height - font_size[1] * 1.1),
            title_text,
            (255, 255, 255),
            font=title_font
        )
        image_editable.text(
            (0, 1 * image.height - font_size[1] * 1.1),
            title_text,
            (255, 255, 255),
            font=title_font
        )

        if ratio is not None:
            new_width = int(image.height * ratio)
            image = image.resize((new_width, image.height), PIL.Image.NEAREST)
        else:
            image = image.resize((image.width, image.height), PIL.Image.NEAREST)

        img_byte_arr = io.BytesIO()

        try:
            image.save(img_byte_arr, format=extension, quality=100, optimize=True)
        except KeyError:
            return False

        blurhash_ = blurhash.encode(img_byte_arr, x_components=4, y_components=3)
        blur_image = blurhash.decode(blurhash_, image.width, image.height)

        if isinstance(schema_in, dict):
            try:
                schema_in["hash"] = img_2_b64(blur_image)
                schema_in["file_name"] = new_name
                schema_in["extension"] = extension
            except KeyError:
                return False
        else:
            if not (hasattr(schema_in, "file_name") and hasattr(schema_in, "extension")):
                return False

            schema_in.file_name = new_name
            schema_in.extension = extension
            schema_in.hash = img_2_b64(blur_image)

        async with aiofiles.open(os.path.join(base_dir, IMAGE_DIR, file.filename), mode='wb') as f:
            await f.write(img_byte_arr.getvalue())

        return True

    async def can_i_do(self, clean_user_depends=False, accept_zero_depends=False, **kwargs):
        copy_depends = self.api.depends.copy()

        if clean_user_depends:
            key_to_delete = None
            for key in copy_depends.keys():
                if isinstance(key, CRUDUser):
                    key_to_delete = key
                    break

            if key_to_delete is not None:
                del copy_depends[key_to_delete]

        is_mine = await check_depends(
            copy_depends,
            kwargs.get("current_user"),
            kwargs.get("data_before_transformation"),
        )

        if accept_zero_depends:
            if not (is_mine or len(copy_depends) == 0):
                if kwargs.get("no_raise", False):
                    return False
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="could not validate depends (accept zero).",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
        else:
            if not is_mine:
                if kwargs.get("no_raise", False):
                    return False
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="could not validate depends.",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
        return True

    async def image_process(self, **kwargs):
        return await self.create_image(kwargs.get("schema_in"), kwargs.get("file"))

    def check_current_user(self, **kwargs):
        user = kwargs.get("current_user", fUser)

        if kwargs.get("request").method.lower() in (
                "post", "put", "patch", "delete"
        ) and kwargs.get("mode", None) != "get_multi_filters" \
                and kwargs.get("mode", None) != "get_multi_filters_own" \
                and kwargs.get("mode", None) != "get_exists_filters" \
                and isinstance(user, FakeUser) and self.api.user_id_field is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="current user is empty so you can't do this action",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if (
                (
                        kwargs.get("request", "").method.lower()
                        in (
                                action.lower() for action in
                                self.api.actions_super_user
                        )
                )
                or
                (
                        kwargs.get("mode", "").lower()
                        in (
                                action.lower() for action in
                                self.api.actions_super_user
                        )
                )
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="current user can do this admin action",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return True
