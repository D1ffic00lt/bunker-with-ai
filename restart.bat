@echo off
cd /d %~dp0
docker-compose restart -t 5 bot