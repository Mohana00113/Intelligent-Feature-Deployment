from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import FeatureFlagType

_ALLOWED_ENVIRONMENT_IDS = {1, 2, 3}


class EnvironmentCreate(BaseModel):
    """Schema used to create a persistent environment."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=100, description="Display name of the environment.")
    key: str = Field(..., min_length=1, max_length=100, description="Stable key used by the API and evaluation engine.")
    description: Optional[str] = Field(default=None, description="Optional summary for the environment.")

    @field_validator("key")
    @classmethod
    def normalize_key(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("Environment key cannot be empty.")
        return normalized


class EnvironmentUpdate(BaseModel):
    """Schema used to update an existing environment."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Updated environment display name.")
    key: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Updated environment key.")
    description: Optional[str] = Field(default=None, description="Updated description.")

    @field_validator("key")
    @classmethod
    def normalize_key(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("Environment key cannot be empty.")
        return normalized

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "EnvironmentUpdate":
        if not any(value is not None for value in (self.name, self.key, self.description)):
            raise ValueError("At least one field must be provided for update.")
        return self


class EnvironmentResponse(BaseModel):
    """Environment representation returned by the API."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int = Field(..., gt=0, description="Primary key of the environment record.")
    name: str = Field(..., min_length=1, max_length=100, description="Display name of the environment.")
    key: str = Field(..., min_length=1, max_length=100, description="Stable key for the environment.")
    description: Optional[str] = Field(default=None, description="Optional environment description.")
    created_at: datetime
    updated_at: datetime


class FlagEnvironmentOverrideBase(BaseModel):
    """Shared fields for environment-specific flag overrides."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(default=True, description="Whether the flag is enabled for the environment.")
    default_value: Any = Field(default=False, description="Environment-specific fallback value for the flag.")
    rollout_percentage: int = Field(default=0, ge=0, le=100, description="Environment-specific rollout percentage.")
    target_users: list[str] = Field(default_factory=list, description="Environment-specific targeted users.")
    target_groups: list[str] = Field(default_factory=list, description="Environment-specific targeted groups.")
    description: Optional[str] = Field(default=None, description="Optional notes for this override.")


class FlagEnvironmentOverrideCreate(FlagEnvironmentOverrideBase):
    """Schema used to create a flag override for a given environment."""

    environment_id: int = Field(..., gt=0, description="Environment id for the override.")

    @field_validator("environment_id")
    @classmethod
    def validate_environment_id(cls, value: int) -> int:
        if value not in _ALLOWED_ENVIRONMENT_IDS:
            raise ValueError("Invalid environment_id. Supported values are 1 (Development), 2 (Staging), 3 (Production).")
        return value


class FlagEnvironmentOverrideUpdate(FlagEnvironmentOverrideBase):
    """Schema used to update an environment-specific override."""

    enabled: Optional[bool] = Field(default=None, description="Whether the flag is enabled for the environment.")
    default_value: Optional[Any] = Field(default=None, description="Environment-specific fallback value for the flag.")
    rollout_percentage: Optional[int] = Field(default=None, ge=0, le=100, description="Environment-specific rollout percentage.")
    target_users: Optional[list[str]] = Field(default=None, description="Environment-specific targeted users.")
    target_groups: Optional[list[str]] = Field(default=None, description="Environment-specific targeted groups.")
    description: Optional[str] = Field(default=None, description="Optional notes for this override.")

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "FlagEnvironmentOverrideUpdate":
        if not any(
            value is not None for value in (
                self.enabled,
                self.default_value,
                self.rollout_percentage,
                self.target_users,
                self.target_groups,
                self.description,
            )
        ):
            raise ValueError("At least one field must be provided for update.")
        return self


class FlagEnvironmentOverrideResponse(FlagEnvironmentOverrideBase):
    """Environment override response returned by the API."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int = Field(..., gt=0, description="Primary key of the override row.")
    flag_id: int = Field(..., gt=0, description="Feature flag id.")
    environment_id: int = Field(..., gt=0, description="Environment id for the override.")
    created_at: datetime
    updated_at: datetime


class FlagCreate(BaseModel):
    """Schema used to create a new feature flag record.

    The API validates that the incoming payload contains a unique flag key,
    a supported flag type, and a default value that matches the declared type.
    """

    model_config = ConfigDict(extra="forbid")

    key: str = Field(..., min_length=1, max_length=100, description="Unique feature flag identifier.")
    type: FeatureFlagType = Field(..., description="Runtime type of the feature flag value.")
    default_value: Any = Field(..., description="Fallback value used when the flag is evaluated.")
    enabled: bool = Field(default=True, description="Whether the flag is enabled for the target environment.")
    rollout_percentage: int = Field(default=0, ge=0, le=100, description="Percentage of users that should receive the feature flag.")
    description: Optional[str] = Field(default=None, description="Optional business context or rollout notes.")
    owner_team: str = Field(..., min_length=1, max_length=100, description="Team responsible for the flag.")
    environment_id: int = Field(..., description="Environment identifier this flag belongs to.")
    target_users: list[str] = Field(default_factory=list, description="List of user IDs explicitly targeted for this flag.")
    target_groups: list[str] = Field(default_factory=list, description="List of group names explicitly targeted for this flag.")

    @field_validator("environment_id")
    def validate_environment_id(cls, value: int) -> int:
        if value not in _ALLOWED_ENVIRONMENT_IDS:
            raise ValueError("Invalid environment_id. Supported values are 1 (Development), 2 (Staging), 3 (Production).")
        return value

    @model_validator(mode="after")
    def validate_default_value_matches_type(self) -> "FlagCreate":
        """Ensure the default value is compatible with the declared flag type."""

        flag_type = self.type
        value = self.default_value

        if flag_type == FeatureFlagType.BOOLEAN:
            if not isinstance(value, bool):
                raise ValueError("default_value must be a boolean when type is 'boolean'.")
        elif flag_type == FeatureFlagType.STRING:
            if not isinstance(value, str):
                raise ValueError("default_value must be a string when type is 'string'.")
        elif flag_type == FeatureFlagType.NUMBER:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("default_value must be a number when type is 'number'.")

        return self


class FlagUpdate(BaseModel):
    """Schema used to update an existing feature flag.

    All fields are optional, but at least one field must be supplied so the API
    does not accept empty update requests.
    """

    model_config = ConfigDict(extra="forbid")

    key: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Updated unique feature flag identifier.")
    type: Optional[FeatureFlagType] = Field(default=None, description="Updated runtime type of the flag.")
    default_value: Optional[Any] = Field(default=None, description="Updated fallback value for the flag.")
    enabled: Optional[bool] = Field(default=None, description="Updated enabled/disabled state.")
    rollout_percentage: Optional[int] = Field(default=None, ge=0, le=100, description="Updated percentage of users that should receive the flag.")
    description: Optional[str] = Field(default=None, description="Updated business context or rollout notes.")
    owner_team: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Updated team responsible for the flag.")
    environment_id: Optional[int] = Field(default=None, description="Updated environment identifier for the flag.")
    target_users: Optional[list[str]] = Field(default=None, description="Updated list of user IDs targeted for this flag.")
    target_groups: Optional[list[str]] = Field(default=None, description="Updated list of group names targeted for this flag.")

    @field_validator("environment_id")
    def validate_environment_id(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return value
        if value not in _ALLOWED_ENVIRONMENT_IDS:
            raise ValueError("Invalid environment_id. Supported values are 1 (Development), 2 (Staging), 3 (Production).")
        return value

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "FlagUpdate":
        """Prevent empty PATCH-style update payloads from being accepted."""

        if not any(
            value is not None
            for value in (
                self.key,
                self.type,
                self.default_value,
                self.enabled,
                self.rollout_percentage,
                self.description,
                self.owner_team,
                self.environment_id,
                self.target_users,
                self.target_groups,
            )
        ):
            raise ValueError("At least one field must be provided for update.")

        return self

    @model_validator(mode="after")
    def validate_default_value_matches_type(self) -> "FlagUpdate":
        """Ensure the new default value remains compatible with the updated type."""

        if self.type is None and self.default_value is None:
            return self

        flag_type = self.type
        value = self.default_value

        if flag_type is None:
            return self

        if flag_type == FeatureFlagType.BOOLEAN:
            if value is not None and not isinstance(value, bool):
                raise ValueError("default_value must be a boolean when type is 'boolean'.")
        elif flag_type == FeatureFlagType.STRING:
            if value is not None and not isinstance(value, str):
                raise ValueError("default_value must be a string when type is 'string'.")
        elif flag_type == FeatureFlagType.NUMBER:
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
                raise ValueError("default_value must be a number when type is 'number'.")

        return self


class FlagResponse(BaseModel):
    """Schema used to return a single feature flag record to the client.

    The `from_attributes=True` option allows the response model to be created
    directly from a SQLAlchemy ORM model instance, which is convenient for
    FastAPI response serialization.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int = Field(..., gt=0, description="Primary key of the feature flag record.")
    key: str = Field(..., min_length=1, max_length=100, description="Unique feature flag identifier.")
    type: FeatureFlagType = Field(..., description="Runtime type of the feature flag value.")
    default_value: Any = Field(..., description="Fallback value used when the flag is evaluated.")
    enabled: bool = Field(..., description="Whether the flag is enabled for the target environment.")
    rollout_percentage: int = Field(default=0, ge=0, le=100, description="Percentage of users that should receive the flag.")
    description: Optional[str] = Field(default=None, description="Optional business context or rollout notes.")
    owner_team: str = Field(..., min_length=1, max_length=100, description="Team responsible for the flag.")
    environment_id: int = Field(..., gt=0, description="Environment identifier this flag belongs to.")
    target_users: list[str] = Field(default_factory=list, description="List of user IDs explicitly targeted for this flag.")
    target_groups: list[str] = Field(default_factory=list, description="List of group names explicitly targeted for this flag.")


class FlagEvaluationResponse(BaseModel):
    """Schema used to return the resolved evaluation state for a feature flag."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(..., min_length=1, max_length=100, description="Resolved feature flag identifier.")
    environment: str = Field(..., min_length=0, description="Requested environment name.")
    enabled: bool = Field(..., description="Resolved enabled state for the requested environment.")
    default_value: Any = Field(..., description="Resolved fallback value for the feature flag.")
    reason: Optional[str] = Field(default=None, description="Reason the evaluation resolved to a particular enabled state.")


class FlagEvaluationRequest(BaseModel):
    """Runtime inputs used to evaluate a feature flag."""

    model_config = ConfigDict(extra="forbid")

    flag_key: str = Field(..., min_length=1, max_length=100)
    environment: str = Field(..., min_length=1, max_length=100)
    user_id: str = Field(..., min_length=1, max_length=100)
    group: Optional[str] = Field(default=None, min_length=1, max_length=100)


class RuntimeFlagEvaluationResponse(BaseModel):
    """Resolved value and rule source for a runtime evaluation request."""

    model_config = ConfigDict(extra="forbid")

    flag_key: str = Field(..., min_length=1, max_length=100)
    value: Any
    source: str = Field(..., pattern="^(user_targeting|group_targeting|percentage_rollout|environment_override|default)$")
    environment: str = Field(..., min_length=1, max_length=100)
    cached: bool = Field(default=False, description="Whether the result was served from the evaluation cache.")


class AuditLogResponse(BaseModel):
    """Audit event returned by the audit log API."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    timestamp: datetime
    actor: str
    environment: Optional[str] = None
    flag_key: str
    action: str
    previous_state: Optional[dict[str, Any]] = None
    new_state: Optional[dict[str, Any]] = None
    diff: dict[str, Any]


class FlagCreate(BaseModel):
    """Schema used to create a new feature flag record.

    The API validates that the incoming payload contains a unique flag key,
    a supported flag type, and a default value that matches the declared type.
    """

    model_config = ConfigDict(extra="forbid")

    key: str = Field(..., min_length=1, max_length=100, description="Unique feature flag identifier.")
    type: FeatureFlagType = Field(..., description="Runtime type of the feature flag value.")
    default_value: Any = Field(..., description="Fallback value used when the flag is evaluated.")
    enabled: bool = Field(default=True, description="Whether the flag is enabled for the target environment.")
    rollout_percentage: int = Field(default=0, ge=0, le=100, description="Percentage of users that should receive the feature flag.")
    description: Optional[str] = Field(default=None, description="Optional business context or rollout notes.")
    owner_team: str = Field(..., min_length=1, max_length=100, description="Team responsible for the flag.")
    environment_id: int = Field(..., description="Environment identifier this flag belongs to.")
    target_users: list[str] = Field(default_factory=list, description="List of user IDs explicitly targeted for this flag.")
    target_groups: list[str] = Field(default_factory=list, description="List of group names explicitly targeted for this flag.")

    @field_validator("environment_id")
    def validate_environment_id(cls, value: int) -> int:
        if value not in _ALLOWED_ENVIRONMENT_IDS:
            raise ValueError("Invalid environment_id. Supported values are 1 (Development), 2 (Staging), 3 (Production).")
        return value

    @model_validator(mode="after")
    def validate_default_value_matches_type(self) -> "FlagCreate":
        """Ensure the default value is compatible with the declared flag type."""

        flag_type = self.type
        value = self.default_value

        if flag_type == FeatureFlagType.BOOLEAN:
            if not isinstance(value, bool):
                raise ValueError("default_value must be a boolean when type is 'boolean'.")
        elif flag_type == FeatureFlagType.STRING:
            if not isinstance(value, str):
                raise ValueError("default_value must be a string when type is 'string'.")
        elif flag_type == FeatureFlagType.NUMBER:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("default_value must be a number when type is 'number'.")

        return self


class FlagUpdate(BaseModel):
    """Schema used to update an existing feature flag.

    All fields are optional, but at least one field must be supplied so the API
    does not accept empty update requests.
    """

    model_config = ConfigDict(extra="forbid")

    key: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Updated unique feature flag identifier.")
    type: Optional[FeatureFlagType] = Field(default=None, description="Updated runtime type of the flag.")
    default_value: Optional[Any] = Field(default=None, description="Updated fallback value for the flag.")
    enabled: Optional[bool] = Field(default=None, description="Updated enabled/disabled state.")
    rollout_percentage: Optional[int] = Field(default=None, ge=0, le=100, description="Updated percentage of users that should receive the flag.")
    description: Optional[str] = Field(default=None, description="Updated business context or rollout notes.")
    owner_team: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Updated team responsible for the flag.")
    environment_id: Optional[int] = Field(default=None, description="Updated environment identifier for the flag.")
    target_users: Optional[list[str]] = Field(default=None, description="Updated list of user IDs targeted for this flag.")
    target_groups: Optional[list[str]] = Field(default=None, description="Updated list of group names targeted for this flag.")

    @field_validator("environment_id")
    def validate_environment_id(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return value
        if value not in _ALLOWED_ENVIRONMENT_IDS:
            raise ValueError("Invalid environment_id. Supported values are 1 (Development), 2 (Staging), 3 (Production).")
        return value

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "FlagUpdate":
        """Prevent empty PATCH-style update payloads from being accepted."""

        if not any(
            value is not None
            for value in (
                self.key,
                self.type,
                self.default_value,
                self.enabled,
                self.rollout_percentage,
                self.description,
                self.owner_team,
                self.environment_id,
                self.target_users,
                self.target_groups,
            )
        ):
            raise ValueError("At least one field must be provided for update.")

        return self

    @model_validator(mode="after")
    def validate_default_value_matches_type(self) -> "FlagUpdate":
        """Ensure the new default value remains compatible with the updated type."""

        if self.type is None and self.default_value is None:
            return self

        flag_type = self.type
        value = self.default_value

        if flag_type is None:
            return self

        if flag_type == FeatureFlagType.BOOLEAN:
            if value is not None and not isinstance(value, bool):
                raise ValueError("default_value must be a boolean when type is 'boolean'.")
        elif flag_type == FeatureFlagType.STRING:
            if value is not None and not isinstance(value, str):
                raise ValueError("default_value must be a string when type is 'string'.")
        elif flag_type == FeatureFlagType.NUMBER:
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
                raise ValueError("default_value must be a number when type is 'number'.")

        return self


class FlagResponse(BaseModel):
    """Schema used to return a single feature flag record to the client.

    The `from_attributes=True` option allows the response model to be created
    directly from a SQLAlchemy ORM model instance, which is convenient for
    FastAPI response serialization.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int = Field(..., gt=0, description="Primary key of the feature flag record.")
    key: str = Field(..., min_length=1, max_length=100, description="Unique feature flag identifier.")
    type: FeatureFlagType = Field(..., description="Runtime type of the feature flag value.")
    default_value: Any = Field(..., description="Fallback value used when the flag is evaluated.")
    enabled: bool = Field(..., description="Whether the flag is enabled for the target environment.")
    rollout_percentage: int = Field(default=0, ge=0, le=100, description="Percentage of users that should receive the flag.")
    description: Optional[str] = Field(default=None, description="Optional business context or rollout notes.")
    owner_team: str = Field(..., min_length=1, max_length=100, description="Team responsible for the flag.")
    environment_id: int = Field(..., gt=0, description="Environment identifier this flag belongs to.")
    target_users: list[str] = Field(default_factory=list, description="List of user IDs explicitly targeted for this flag.")
    target_groups: list[str] = Field(default_factory=list, description="List of group names explicitly targeted for this flag.")


class FlagEvaluationResponse(BaseModel):
    """Schema used to return the resolved evaluation state for a feature flag."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(..., min_length=1, max_length=100, description="Resolved feature flag identifier.")
    environment: str = Field(..., min_length=0, description="Requested environment name.")
    enabled: bool = Field(..., description="Resolved enabled state for the requested environment.")
    default_value: Any = Field(..., description="Resolved fallback value for the feature flag.")
    reason: Optional[str] = Field(default=None, description="Reason the evaluation resolved to a particular enabled state.")
