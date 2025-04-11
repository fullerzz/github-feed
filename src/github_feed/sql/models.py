from datetime import datetime
from enum import Enum

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class RunData(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    executed_at: datetime


class Release(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    html_url: str
    assets_url: str
    tarball_url: str
    zipball_url: str
    node_id: str
    tag_name: str
    target_commitish: str
    name: str | None = None
    body: str
    draft: bool = False
    prelease: bool = False
    created_at: datetime
    published_at: datetime


class User(SQLModel, table=True):
    login: str
    id: int | None = Field(default=None, primary_key=True)
    user_view_type: str | None = None
    node_id: str
    avatar_url: str | None
    gravatar_id: str | None
    url: str | None
    html_url: str | None
    followers_url: str | None
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: str | None
    organizations_url: str | None
    repos_url: str | None
    events_url: str
    received_events_url: str | None
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


class SquashMergeCommitTitle(Enum):
    PR_TITLE = "PR_TITLE"
    COMMIT_OR_PR_TITLE = "COMMIT_OR_PR_TITLE"


class SquashMergeCommitMessage(Enum):
    PR_BODY = "PR_BODY"
    COMMIT_MESSAGES = "COMMIT_MESSAGES"
    BLANK = "BLANK"


class MergeCommitTitle(Enum):
    PR_TITLE = "PR_TITLE"
    MERGE_MESSAGE = "MERGE_MESSAGE"


class MergeCommitMessage(Enum):
    PR_BODY = "PR_BODY"
    PR_TITLE = "PR_TITLE"
    BLANK = "BLANK"


class Repository(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    node_id: str
    name: str
    full_name: str
    forks: int
    private: bool = Field(..., description="Whether the repository is private or public.")
    html_url: str
    description: str | None = None
    fork: bool
    url: str | None = None
    assignees_url: str
    blobs_url: str
    branches_url: str
    collaborators_url: str
    comments_url: str
    commits_url: str
    compare_url: str
    contents_url: str
    contributors_url: str | None = None
    deployments_url: str | None = None
    downloads_url: str | None = None
    events_url: str | None = None
    forks_url: str | None = None
    git_commits_url: str
    git_refs_url: str
    git_tags_url: str
    git_url: str
    issue_comment_url: str
    issue_events_url: str
    issues_url: str
    keys_url: str
    labels_url: str
    languages_url: str | None = None
    merges_url: str | None = None
    milestones_url: str
    notifications_url: str
    pulls_url: str
    releases_url: str
    ssh_url: str
    stargazers_url: str | None = None
    statuses_url: str
    subscribers_url: str | None = None
    tags_url: str | None = None
    trees_url: str
    homepage: str | None = None
    language: str | None
    forks_count: int
    stargazers_count: int
    watchers_count: int
    size: int
    default_branch: str
    open_issues_count: int
    has_issues: bool
    has_pages: bool
    has_downloads: bool
    archived: bool = Field(..., description="Whether the repository is archived.")
    disabled: bool = Field(..., description="Returns whether or not this repository disabled.")
    visibility: str | None = Field(
        "public", description="The repository visibility: public, private, or internal."
    )
    pushed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    open_issues: int
    watchers: int
    master_branch: str | None = None
    starred_at: str | None = None
