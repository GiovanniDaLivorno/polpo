
# simple example of how to use Polpo in an application.
# polpo directory should be in the Python path when running this example
# - either run from the project root, or
# - via PYTHONPATH environment variable
import asyncio
from Polpo import Polpo

async def main():
    polpo = Polpo()
    response = await polpo.run("Check recent ERROR logs and tell me main issues.")
    print("\n=== FINAL ANSWER ===\n")
    print(response)

asyncio.run(main())