#!/usr/bin/env python3
"""
Detailed investigation of Euler subgraphs to understand the data available
and determine if EulerSwap data exists or if we need alternative approaches.
"""

import asyncio
import os

from dotenv import load_dotenv
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

# Load environment variables
load_dotenv()


async def investigate_subgraph_data(subgraph_id: str, name: str):
    """Deep dive into subgraph data structure and sample data."""
    print(f"\n{'='*80}")
    print(f"DETAILED INVESTIGATION: {name}")
    print(f"Subgraph ID: {subgraph_id}")
    print(f"{'='*80}")

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

        # Get full schema information
        schema_query = gql("""
        query GetSchema {
          __schema {
            queryType {
              fields {
                name
                description
                type {
                  name
                  kind
                }
              }
            }
          }
        }
        """)

        print("📋 Fetching complete schema...")
        schema_result = await client.execute_async(schema_query)

        # Analyze available query fields
        fields = schema_result["__schema"]["queryType"]["fields"]
        print(f"\n🔍 Found {len(fields)} query fields:")

        # Group fields by category
        vault_fields = []
        market_fields = []
        borrow_fields = []
        other_fields = []

        for field in fields:
            field_name = field["name"]
            if "vault" in field_name.lower():
                vault_fields.append(field_name)
            elif "market" in field_name.lower():
                market_fields.append(field_name)
            elif "borrow" in field_name.lower():
                borrow_fields.append(field_name)
            else:
                other_fields.append(field_name)

        print(f"\n🏦 Vault-related fields ({len(vault_fields)}):")
        for field in vault_fields:
            print(f"  - {field}")

        print(f"\n📈 Market-related fields ({len(market_fields)}):")
        for field in market_fields:
            print(f"  - {field}")

        print(f"\n💰 Borrow-related fields ({len(borrow_fields)}):")
        for field in borrow_fields:
            print(f"  - {field}")

        print(f"\n🔧 Other fields ({len(other_fields)}):")
        for field in other_fields[:10]:  # Show first 10 to avoid clutter
            print(f"  - {field}")
        if len(other_fields) > 10:
            print(f"  ... and {len(other_fields) - 10} more")

        # Try to fetch sample data from key entities
        print("\n📊 SAMPLE DATA INVESTIGATION")
        print("-" * 50)

        # Test queries based on available fields
        test_queries = []

        if vault_fields:
            # Try the first vault-related field
            main_vault_field = vault_fields[0]
            if not main_vault_field.endswith(
                "_filter"
            ) and not main_vault_field.endswith("_orderBy"):
                test_queries.append(
                    (
                        f"Sample {main_vault_field}",
                        f"""
                query Sample {{
                  {main_vault_field}(first: 3) {{
                    id
                  }}
                }}
                """,
                    )
                )

        if market_fields:
            # Try market data
            main_market_field = [
                f
                for f in market_fields
                if not f.endswith("_filter") and not f.endswith("_orderBy")
            ][0]
            test_queries.append(
                (
                    f"Sample {main_market_field}",
                    f"""
            query Sample {{
              {main_market_field}(first: 3) {{
                id
              }}
            }}
            """,
                )
            )

        # Execute test queries
        for query_name, query_str in test_queries:
            try:
                print(f"\n🧪 {query_name}...")
                query = gql(query_str)
                result = await client.execute_async(query)

                # Extract the data
                data_key = list(result.keys())[0]
                data = result[data_key]

                print(f"  ✅ Found {len(data)} records")
                if data:
                    print(f"  📝 Sample record: {data[0]}")
                else:
                    print("  📝 No data found")

            except Exception as e:
                print(f"  ❌ Error: {str(e)}")

        # Look for any EulerSwap indicators
        print("\n🔍 EULERSWAP INDICATORS")
        print("-" * 30)

        eulerswap_indicators = []
        for field in fields:
            field_name = field["name"]
            description = field.get("description", "")

            # Look for swap, AMM, or liquidity related terms
            if any(
                keyword in field_name.lower()
                for keyword in ["swap", "amm", "liquidity", "pool"]
            ):
                eulerswap_indicators.append((field_name, description))

        if eulerswap_indicators:
            print(
                f"✅ Found {len(eulerswap_indicators)} potential EulerSwap indicators:"
            )
            for field_name, description in eulerswap_indicators:
                print(f"  - {field_name}: {description}")
        else:
            print("❌ No clear EulerSwap/AMM indicators found")

        return True

    except Exception as e:
        print(f"❌ Failed to investigate {name}: {str(e)}")
        return False


async def main():
    """Investigate both subgraphs in detail."""
    print("🔬 DETAILED EULER SUBGRAPH INVESTIGATION")
    print("🎯 Goal: Find EulerSwap AMM/DEX data for delta-neutral strategies")
    print("=" * 80)

    # Subgraph information
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

    results = {}
    for subgraph_id, name in subgraphs:
        success = await investigate_subgraph_data(subgraph_id, name)
        results[name] = success

    # Final analysis
    print(f"\n{'='*80}")
    print("📋 INVESTIGATION SUMMARY")
    print(f"{'='*80}")

    for name, success in results.items():
        status = "✅ Successfully analyzed" if success else "❌ Failed to analyze"
        print(f"{name}: {status}")

    print("\n🎯 RECOMMENDATIONS FOR DELTA-NEUTRAL STRATEGY:")
    print("1. Neither subgraph appears to have traditional DEX/AMM data")
    print("2. EulerSwap might be too new to be indexed by these subgraphs")
    print("3. Alternative approaches:")
    print("   • Look for EulerSwap-specific subgraphs")
    print("   • Use direct smart contract event logs")
    print("   • Generate synthetic data for backtesting demonstration")
    print("   • Focus on Euler lending rates + external price feeds")

    print("\n💡 NEXT STEPS:")
    print("1. Search The Graph explorer for 'EulerSwap' specifically")
    print("2. Check Euler GitHub for subgraph configurations")
    print("3. Implement backup strategy with synthetic data")
    print("4. Use community subgraph for vault data + external price feeds")


if __name__ == "__main__":
    asyncio.run(main())
