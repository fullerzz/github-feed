from datetime import datetime
from enum import Enum
from typing import NotRequired, TypedDict

from pydantic import BaseModel, EmailStr, Field


class LinkHeader(BaseModel):
    next: str | None = None
    last: str | None = None
    first: str | None = None
    prev: str | None = None


class User(BaseModel):
    login: str
    id: int
    user_view_type: str | None = None
    node_id: str
    avatar_url: str
    gravatar_id: str | None
    url: str
    html_url: str
    followers_url: str
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: str
    organizations_url: str
    repos_url: str
    events_url: str
    received_events_url: str
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


class License(TypedDict):
    key: str
    name: str
    url: str | None
    html_url: NotRequired[str | None]


class Permissions(TypedDict):
    admin: bool
    pull: bool
    triage: NotRequired[str | None]
    push: bool
    maintain: NotRequired[str | None]


class Owner(TypedDict):
    name: NotRequired[str | None]
    email: NotRequired[str | None]
    login: str
    id: int
    node_id: str
    avatar_url: str
    gravatar_id: NotRequired[str | None]
    url: str
    html_url: str
    followers_url: str
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: str
    organizations_url: str
    repos_url: str
    events_url: str
    received_events_url: str
    type: str
    site_admin: bool
    starred_at: NotRequired[str | None]
    user_view_type: NotRequired[str | None]


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


class Repository(BaseModel):
    id: int = Field(..., description="Unique identifier of the repository", examples=[42])
    node_id: str = Field(..., examples=["MDEwOlJlcG9zaXRvcnkxMjk2MjY5"])
    name: str = Field(..., description="The name of the repository.", examples=["Team Environment"])
    full_name: str = Field(..., examples=["octocat/Hello-World"])
    license: License | None
    forks: int
    permissions: Permissions | None = None
    owner: Owner = Field(..., description="A GitHub user.", title="Simple User")
    private: bool = Field(..., description="Whether the repository is private or public.")
    html_url: str = Field(..., examples=["https://github.com/octocat/Hello-World"])
    description: str | None = Field(..., examples=["This your first repo!"])
    fork: bool
    url: str = Field(..., examples=["https://api.github.com/repos/octocat/Hello-World"])
    archive_url: str = Field(
        ...,
        examples=["http://api.github.com/repos/octocat/Hello-World/{archive_format}{/ref}"],
    )
    assignees_url: str = Field(
        ...,
        examples=["http://api.github.com/repos/octocat/Hello-World/assignees{/user}"],
    )
    blobs_url: str = Field(
        ...,
        examples=["http://api.github.com/repos/octocat/Hello-World/git/blobs{/sha}"],
    )
    branches_url: str = Field(
        ...,
        examples=["http://api.github.com/repos/octocat/Hello-World/branches{/branch}"],
    )
    collaborators_url: str = Field(
        ...,
        examples=["http://api.github.com/repos/octocat/Hello-World/collaborators{/collaborator}"],
    )
    comments_url: str = Field(
        ...,
        examples=["http://api.github.com/repos/octocat/Hello-World/comments{/number}"],
    )
    commits_url: str = Field(..., examples=["http://api.github.com/repos/octocat/Hello-World/commits{/sha}"])
    compare_url: str = Field(
        ...,
        examples=["http://api.github.com/repos/octocat/Hello-World/compare/{base}...{head}"],
    )
    contents_url: str = Field(
        ...,
        examples=["http://api.github.com/repos/octocat/Hello-World/contents/{+path}"],
    )
    contributors_url: str = Field(
        ..., examples=["http://api.github.com/repos/octocat/Hello-World/contributors"]
    )
    deployments_url: str = Field(
        ..., examples=["http://api.github.com/repos/octocat/Hello-World/deployments"]
    )
    downloads_url: str = Field(..., examples=["http://api.github.com/repos/octocat/Hello-World/downloads"])
    events_url: str = Field(..., examples=["http://api.github.com/repos/octocat/Hello-World/events"])
    forks_url: str = Field(..., examples=["http://api.github.com/repos/octocat/Hello-World/forks"])
    git_commits_url: str = Field(
        ...,
        examples=["http://api.github.com/repos/octocat/Hello-World/git/commits{/sha}"],
    )
    git_refs_url: str = Field(
        ..., examples=["http://api.github.com/repos/octocat/Hello-World/git/refs{/sha}"]
    )
    git_tags_url: str = Field(
        ..., examples=["http://api.github.com/repos/octocat/Hello-World/git/tags{/sha}"]
    )
    git_url: str = Field(..., examples=["git:github.com/octocat/Hello-World.git"])
    issue_comment_url: str = Field(
        ...,
        examples=["http://api.github.com/repos/octocat/Hello-World/issues/comments{/number}"],
    )
    issue_events_url: str = Field(
        ...,
        examples=["http://api.github.com/repos/octocat/Hello-World/issues/events{/number}"],
    )
    issues_url: str = Field(
        ...,
        examples=["http://api.github.com/repos/octocat/Hello-World/issues{/number}"],
    )
    keys_url: str = Field(..., examples=["http://api.github.com/repos/octocat/Hello-World/keys{/key_id}"])
    labels_url: str = Field(..., examples=["http://api.github.com/repos/octocat/Hello-World/labels{/name}"])
    languages_url: str = Field(..., examples=["http://api.github.com/repos/octocat/Hello-World/languages"])
    merges_url: str = Field(..., examples=["http://api.github.com/repos/octocat/Hello-World/merges"])
    milestones_url: str = Field(
        ...,
        examples=["http://api.github.com/repos/octocat/Hello-World/milestones{/number}"],
    )
    notifications_url: str = Field(
        ...,
        examples=["http://api.github.com/repos/octocat/Hello-World/notifications{?since,all,participating}"],
    )
    pulls_url: str = Field(..., examples=["http://api.github.com/repos/octocat/Hello-World/pulls{/number}"])
    releases_url: str = Field(..., examples=["http://api.github.com/repos/octocat/Hello-World/releases{/id}"])
    ssh_url: str = Field(..., examples=["git@github.com:octocat/Hello-World.git"])
    stargazers_url: str = Field(..., examples=["http://api.github.com/repos/octocat/Hello-World/stargazers"])
    statuses_url: str = Field(
        ..., examples=["http://api.github.com/repos/octocat/Hello-World/statuses/{sha}"]
    )
    subscribers_url: str = Field(
        ..., examples=["http://api.github.com/repos/octocat/Hello-World/subscribers"]
    )
    subscription_url: str = Field(
        ..., examples=["http://api.github.com/repos/octocat/Hello-World/subscription"]
    )
    tags_url: str = Field(..., examples=["http://api.github.com/repos/octocat/Hello-World/tags"])
    teams_url: str = Field(..., examples=["http://api.github.com/repos/octocat/Hello-World/teams"])
    trees_url: str = Field(
        ...,
        examples=["http://api.github.com/repos/octocat/Hello-World/git/trees{/sha}"],
    )
    clone_url: str = Field(..., examples=["https://github.com/octocat/Hello-World.git"])
    mirror_url: str | None = Field(..., examples=["git:git.example.com/octocat/Hello-World"])
    hooks_url: str = Field(..., examples=["http://api.github.com/repos/octocat/Hello-World/hooks"])
    svn_url: str = Field(..., examples=["https://svn.github.com/octocat/Hello-World"])
    homepage: str | str | None = Field(..., examples=["https://github.com"])
    language: str | None
    forks_count: int = Field(..., examples=[9])
    stargazers_count: int = Field(..., examples=[80])
    watchers_count: int = Field(..., examples=[80])
    size: int = Field(
        ...,
        description="The size of the repository, in kilobytes. Size is calculated hourly. When a repository is initially created, the size is 0.",
        examples=[108],
    )
    default_branch: str = Field(..., description="The default branch of the repository.", examples=["master"])
    open_issues_count: int = Field(..., examples=[0])
    is_template: bool | None = Field(
        False,
        description="Whether this repository acts as a template that can be used to generate new repositories.",
        examples=[True],
    )
    topics: list[str] | None = None
    has_issues: bool = Field(..., description="Whether issues are enabled.", examples=[True])
    has_projects: bool = Field(..., description="Whether projects are enabled.", examples=[True])
    has_wiki: bool = Field(..., description="Whether the wiki is enabled.", examples=[True])
    has_pages: bool
    has_downloads: bool = Field(..., description="Whether downloads are enabled.", examples=[True])
    has_discussions: bool | None = Field(
        False, description="Whether discussions are enabled.", examples=[True]
    )
    archived: bool = Field(..., description="Whether the repository is archived.")
    disabled: bool = Field(..., description="Returns whether or not this repository disabled.")
    visibility: str | None = Field(
        "public", description="The repository visibility: public, private, or internal."
    )
    pushed_at: datetime | None = Field(..., examples=["2011-01-26T19:06:43Z"])
    created_at: datetime | None = Field(..., examples=["2011-01-26T19:01:12Z"])
    updated_at: datetime | None = Field(..., examples=["2011-01-26T19:14:43Z"])
    allow_rebase_merge: bool | None = Field(
        True,
        description="Whether to allow rebase merges for pull requests.",
        examples=[True],
    )
    temp_clone_token: str | None = None
    allow_squash_merge: bool | None = Field(
        True,
        description="Whether to allow squash merges for pull requests.",
        examples=[True],
    )
    allow_auto_merge: bool | None = Field(
        False,
        description="Whether to allow Auto-merge to be used on pull requests.",
        examples=[False],
    )
    delete_branch_on_merge: bool | None = Field(
        False,
        description="Whether to delete head branches when pull requests are merged",
        examples=[False],
    )
    allow_update_branch: bool | None = Field(
        False,
        description="Whether or not a pull request head branch that is behind its base branch can always be updated even if it is not required to be up to date before merging.",
        examples=[False],
    )
    use_squash_pr_title_as_default: bool | None = Field(
        False,
        description="Whether a squash merge commit can use the pull request title as default. **This property is closing down. Please use `squash_merge_commit_title` instead.",
    )
    squash_merge_commit_title: SquashMergeCommitTitle | None = Field(
        None,
        description="The default value for a squash merge commit title:\n\n- `PR_TITLE` - default to the pull request's title.\n- `COMMIT_OR_PR_TITLE` - default to the commit's title (if only one commit) or the pull request's title (when more than one commit).",
    )
    squash_merge_commit_message: SquashMergeCommitMessage | None = Field(
        None,
        description="The default value for a squash merge commit message:\n\n- `PR_BODY` - default to the pull request's body.\n- `COMMIT_MESSAGES` - default to the branch's commit messages.\n- `BLANK` - default to a blank commit message.",
    )
    merge_commit_title: MergeCommitTitle | None = Field(
        None,
        description="The default value for a merge commit title.\n\n- `PR_TITLE` - default to the pull request's title.\n- `MERGE_MESSAGE` - default to the classic title for a merge message (e.g., Merge pull request #123 from branch-name).",
    )
    merge_commit_message: MergeCommitMessage | None = Field(
        None,
        description="The default value for a merge commit message.\n\n- `PR_TITLE` - default to the pull request's title.\n- `PR_BODY` - default to the pull request's body.\n- `BLANK` - default to a blank commit message.",
    )
    allow_merge_commit: bool | None = Field(
        True,
        description="Whether to allow merge commits for pull requests.",
        examples=[True],
    )
    allow_forking: bool | None = Field(None, description="Whether to allow forking this repo")
    web_commit_signoff_required: bool | None = Field(
        False,
        description="Whether to require contributors to sign off on web-based commits",
    )
    open_issues: int
    watchers: int
    master_branch: str | None = None
    starred_at: str | None = Field(None, examples=['"2020-07-09T00:17:42Z"'])
    anonymous_access_enabled: bool | None = Field(
        None, description="Whether anonymous git access is enabled for this repository"
    )


class Release(BaseModel):
    id: int
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
