#!/bin/sh

.venv/bin/uvicorn mock_login.main:app --proxy-headers --host ${HOST} --port ${PORT}
