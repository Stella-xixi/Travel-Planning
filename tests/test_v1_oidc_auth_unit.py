"""OIDC access-token verification and trusted tenant derivation tests."""

from __future__ import annotations

import httpx
import jwt
import pytest
from fastapi import Depends, FastAPI

from backend.travel_planning_api.v1.auth import OIDCAuthenticator, OIDCSettings, require_principal
from backend.travel_planning_api.v1.models import Principal


def build_app(authenticator: OIDCAuthenticator) -> FastAPI:
    app = FastAPI()

    @app.get("/private")
    async def private(principal: Principal = Depends(authenticator)) -> Principal:
        return principal

    return app


def build_default_auth_app() -> FastAPI:
    app = FastAPI()

    @app.get("/private")
    async def private(principal: Principal = Depends(require_principal)) -> Principal:
        return principal

    return app


@pytest.mark.asyncio
async def test_oidc_authenticator_derives_tenant_only_from_verified_claims() -> None:
    async def decode(_token: str):
        return {
            "sub": "user-1",
            "tenant_id": "tenant-1",
            "roles": ["member", "tenant_admin"],
            "authorization_epoch": 7,
        }

    authenticator = OIDCAuthenticator(
        OIDCSettings(
            issuer="https://id.example.com/",
            audience="travel-planning-api",
            jwks_url="https://id.example.com/.well-known/jwks.json",
        ),
        decoder=decode,
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=build_app(authenticator)),
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/private",
            headers={
                "Authorization": "Bearer opaque-test-token",
                "X-Travel-Planning-Dev-Tenant": "attacker-tenant",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "tenant-1"
    assert payload["user_id"] == "user-1"
    assert set(payload["roles"]) == {"member", "tenant_admin"}
    assert payload["authorization_epoch"] == 7


@pytest.mark.asyncio
async def test_oidc_authenticator_fails_closed_without_bearer_or_on_invalid_token() -> None:
    def invalid(_token: str):
        raise jwt.InvalidSignatureError("private verifier detail")

    authenticator = OIDCAuthenticator(
        OIDCSettings(
            issuer="https://id.example.com/",
            audience="travel-planning-api",
            jwks_url="https://id.example.com/.well-known/jwks.json",
        ),
        decoder=invalid,
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=build_app(authenticator)),
        base_url="http://testserver",
    ) as client:
        missing = await client.get("/private")
        rejected = await client.get(
            "/private",
            headers={"Authorization": "Bearer attacker-token"},
        )

    assert missing.status_code == 401
    assert rejected.status_code == 401
    assert "private verifier detail" not in rejected.text


def test_oidc_settings_reject_symmetric_algorithm_configuration() -> None:
    with pytest.raises(ValueError, match="asymmetric"):
        OIDCSettings(
            issuer="https://id.example.com/",
            audience="travel-planning-api",
            jwks_url="https://id.example.com/.well-known/jwks.json",
            algorithms=("HS256",),
        )


def test_oidc_settings_require_https_outside_local_environment(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    with pytest.raises(ValueError, match="HTTPS"):
        OIDCSettings(
            issuer="https://id.example.com/",
            audience="travel-planning-api",
            jwks_url="http://id.example.com/keys",
        )


@pytest.mark.asyncio
async def test_development_bff_secret_authenticates_a_non_loopback_peer(monkeypatch) -> None:
    secret = "travel-planning-local-bff-secret-with-32-bytes"
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("TRAVEL_PLANNING_V1_DEV_AUTH", "1")
    monkeypatch.setenv("TRAVEL_PLANNING_V1_DEV_BFF_SECRET", secret)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(
            app=build_default_auth_app(),
            client=("172.20.0.10", 43100),
        ),
        base_url="http://api",
    ) as client:
        rejected = await client.get(
            "/private",
            headers={
                "X-Travel-Planning-Dev-Tenant": "tenant-1",
                "X-Travel-Planning-Dev-User": "user-1",
            },
        )
        accepted = await client.get(
            "/private",
            headers={
                "X-Travel-Planning-Dev-BFF-Secret": secret,
                "X-Travel-Planning-Dev-Tenant": "tenant-1",
                "X-Travel-Planning-Dev-User": "user-1",
                "X-Travel-Planning-Dev-Roles": "owner,editor",
            },
        )

    assert rejected.status_code == 401
    assert accepted.status_code == 200
    assert accepted.json()["tenant_id"] == "tenant-1"
    assert set(accepted.json()["roles"]) == {"editor", "owner"}


@pytest.mark.asyncio
async def test_development_identity_is_refused_in_production_even_from_loopback(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("TRAVEL_PLANNING_V1_DEV_AUTH", "1")
    monkeypatch.setenv(
        "TRAVEL_PLANNING_V1_DEV_BFF_SECRET",
        "travel-planning-local-bff-secret-with-32-bytes",
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=build_default_auth_app()),
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/private",
            headers={
                "X-Travel-Planning-Dev-BFF-Secret": "travel-planning-local-bff-secret-with-32-bytes",
                "X-Travel-Planning-Dev-Tenant": "tenant-1",
                "X-Travel-Planning-Dev-User": "user-1",
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_development_identity_honors_the_shared_deployment_environment(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("TRAVEL_PLANNING_DEPLOYMENT_ENV", "staging")
    monkeypatch.setenv("TRAVEL_PLANNING_V1_DEV_AUTH", "1")
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=build_default_auth_app()),
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/private",
            headers={
                "X-Travel-Planning-Dev-Tenant": "tenant-1",
                "X-Travel-Planning-Dev-User": "user-1",
            },
        )

    assert response.status_code == 401
