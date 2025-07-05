#!/usr/bin/env python3
"""
Quick test script to investigate both Euler subgraphs and determine
which one contains EulerSwap data vs just Euler Finance lending data.
"""

import asyncio
import os

from dotenv import load_dotenv
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

# Load environment variables
load_dotenv()


async def test_subgraph(subgraph_id: str, name: str):
    """Test a subgraph to see what entities it contains."""
    print(f"\n{'='*60}")
    print(f"Testing {name}: {subgraph_id}")
    print(f"{'='*60}")

    # Get API key from environment
    api_key = os.getenv("thegraph_api_key")
    if not api_key:
        print("❌ Missing thegraph_api_key in .env file")
        return False

    # The Graph gateway endpoint with API key
    endpoint = f"https://gateway.thegraph.com/api/{api_key}/subgraphs/id/{subgraph_id}"

    try:
        transport = AIOHTTPTransport(url=endpoint)
        client = Client(transport=transport, fetch_schema_from_transport=False)

        # Introspection query to see what types are available
        introspection_query = gql("""
        query IntrospectionQuery {
          __schema {
            types {
              name
              kind
              description
            }
          }
        }
        """)

        print("Fetching schema...")
        result = await client.execute_async(introspection_query)

        # Look for relevant types
        types = result["__schema"]["types"]
        relevant_types = []

        for type_info in types:
            name = type_info["name"]
            # Look for swap, pool, liquidity related types
            if any(
                keyword in name.lower()
                for keyword in [
                    "swap",
                    "pool",
                    "liquidity",
                    "vault",
                    "borrow",
                    "lend",
                    "market",
                    "position",
                    "euler",
                    "amm",
                ]
            ):
                relevant_types.append(name)

        print(f"Found {len(relevant_types)} relevant entity types:")
        for t in sorted(relevant_types):
            print(f"  - {t}")

        # Try to fetch some sample data from key entities
        test_queries = []

        # Test for basic swap data
        if any("swap" in t.lower() for t in relevant_types):
            test_queries.append(
                (
                    "Swaps",
                    """
            query TestSwaps {
              swaps(first: 3) {
                id
                blockNumber
                timestamp
              }
            }
            """,
                )
            )

        # Test for pool data
        if any("pool" in t.lower() for t in relevant_types):
            test_queries.append(
                (
                    "Pools",
                    """
            query TestPools {
              pools(first: 3) {
                id
              }
            }
            """,
                )
            )

        # Test for vault data (Euler Finance specific)
        if any("vault" in t.lower() for t in relevant_types):
            test_queries.append(
                (
                    "Vaults",
                    """
            query TestVaults {
              vaults(first: 3) {
                id
              }
            }
            """,
                )
            )

        # Execute test queries
        for query_name, query_str in test_queries:
            try:
                print(f"\nTesting {query_name}...")
                query = gql(query_str)
                result = await client.execute_async(query)
                print(
                    f"  ✅ {query_name}: {len(result.get(query_name.lower(), []))} records found"
                )
                if result.get(query_name.lower()):
                    print(f"     Sample: {result[query_name.lower()][0]}")
            except Exception as e:
                print(f"  ❌ {query_name}: {str(e)}")

        return True

    except Exception as e:
        print(f"❌ Failed to connect to {name}: {str(e)}")
        return False


async def main():
    """Test both Euler subgraphs."""
    print("🔍 Investigating Euler Subgraphs for EulerSwap Data")
    print("=" * 60)

    # Subgraph information from graph.md
    subgraphs = [
        (
            "95nyAWFFaiz6gykko3HtBCyhRuP5vZzuKYsZiLxHxLhr",
            "Official Euler Finance (2 years old)",
        ),
        (
            "7TKfCCjXaAeZSFaGh3ccir8JnQd1K4Rjq75G6KnVQnoP",
            "Community Euler (4 months old)",
        ),
    ]

    results = []
    for subgraph_id, name in subgraphs:
        success = await test_subgraph(subgraph_id, name)
        results.append((name, success))

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for name, success in results:
        status = "✅ Connected" if success else "❌ Failed"
        print(f"{name}: {status}")

    print("\n📝 Next Steps:")
    print("1. Review the entity types found in each subgraph")
    print("2. Choose the subgraph with the most relevant EulerSwap data")
    print("3. Focus on 'swap', 'pool', and 'liquidity' entities")
    print("4. The newer community subgraph (4 months) may have more recent data")


if __name__ == "__main__":
    asyncio.run(main())
