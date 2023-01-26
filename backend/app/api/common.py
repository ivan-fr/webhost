from fastapi import APIRouter

from app import schemas
import app.logic.user

from app.api.base import APIBase
from app.crud import crud_user

router = APIRouter(prefix="/common", tags=["common"])

APIUser = APIBase(
    native_schema=schemas.UserCreate,
    update_schema=schemas.UserUpdate,
    singular="user",
    plural="users",
    router=router,
    crud_=crud_user,
    actions_super_user=["delete", "get_multi_filters"],
    depends={
        "self": {"id": "current_user"},
    },
    user_id_field="id",
    response_model_exclude={"password", "hashed_password", "email"},
    unique_index={"email", "nickname"},
    getter_schema=app.logic.user.UserFilter,
    getter_sanitize=app.logic.user.sanitize_get_request
)

APIArticle = APIBase(
    native_schema=schemas.ArticleCreate,
    update_schema=schemas.ArticleUpdate,
    singular="article",
    plural="articles",
    router=router,
    actions_super_user=[],
    depends={crud_user: {"_id": ["created_by_id", "current_user"]}},
)
