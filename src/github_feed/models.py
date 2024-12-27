from datetime import datetime

from pydantic import AnyUrl, BaseModel, EmailStr, Field


class User(BaseModel):
    login: str
    id: int
    user_view_type: str | None = None
    node_id: str
    avatar_url: AnyUrl
    gravatar_id: str | None
    url: AnyUrl
    html_url: AnyUrl
    followers_url: AnyUrl
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: AnyUrl
    organizations_url: AnyUrl
    repos_url: AnyUrl
    events_url: str
    received_events_url: AnyUrl
    type: str
    site_admin: bool
    name: str | None
    company: str | None
    blog: str | None
    location: str | None
    email: EmailStr | None
    notification_email: EmailStr | None = None
    hireable: bool | None
    bio: str | None
    twitter_username: str | None = None
    public_repos: int
    public_gists: int
    followers: int
    following: int
    created_at: datetime
    updated_at: datetime
    private_gists: int | None = Field(None, examples=[1])
    total_private_repos: int | None = Field(None, examples=[2])
    owned_private_repos: int | None = Field(None, examples=[2])
    disk_usage: int | None = Field(None, examples=[1])
    collaborators: int | None = Field(None, examples=[3])
