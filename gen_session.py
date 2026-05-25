"""
Bir marta ishga tushiring, SESSION_STRING hosil qiling.
Keyin o'sha stringni Render'da SESSION_STRING env variable sifatida qo'shing.
"""
import asyncio
from pyrogram import Client

async def main():
    print("=== Session String Generator ===\n")
    api_id   = int(input("API_ID   : "))
    api_hash = input("API_HASH : ").strip()

    async with Client(":memory:", api_id=api_id, api_hash=api_hash) as app:
        session_string = await app.export_session_string()

    print("\n✅ Mana SESSION_STRING (Render'ga qo'shing):\n")
    print(session_string)
    print()

asyncio.run(main())
