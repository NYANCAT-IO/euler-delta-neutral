Introducing EulerSwap
Introducing EulerSwap
Market makers and liquidity providers (LPs) want more from decentralised exchanges: higher yields, the ability to collateralise LP positions, deeper liquidity for supported assets, and lower costs for rebalancing.

Enter EulerSwap: A new DEX with a built-in AMM supercharged by Euler’s lending infrastructure and integrated with Uniswap v4’s hook architecture, blending the best of two modular powerhouses to unlock the next-gen of DEXs and capital efficiency.

A unified system for swaps, lending, and leverage
EulerSwap integrates directly with Euler’s lending vaults. When a liquidity provider (LP) supplies assets to a trading pair, those assets are deposited into Euler vaults. This means the same capital can:

Facilitate swaps
Earn lending yield
Be used as collateral to borrow other assets
This structure avoids capital fragmentation and allows liquidity to remain productive at all times.

Just-in-time liquidity: simulate up to 50x depth
LP deposits in EulerSwap can be used as collateral natively within Euler, which can be used to support deep just-in-time (JIT) liquidity provision. If an LP doesn't hold enough of the output token, EulerSwap can borrow it on-demand using the input token as collateral. This means LPs don’t need to pre-fund both sides of a pool.

In optimal cases, this mechanism can simulate up to 50x the depth of a traditional AMM. It's especially effective in stable or pegged asset markets where pricing risk is low.

Lending vaults as liquidity hubs
Because assets are deposited into Euler’s lending vaults, a single asset (e.g. USDC) can be used across multiple EulerSwap pools. This turns the lending protocol into a shared liquidity layer, improving capital efficiency across the ecosystem.

Dynamic hedging and impermanent loss protection
Because reserves live inside lending vaults, LPs can borrow against them natively. This makes dynamic hedging practical, enabling delta-neutral strategies for uncorrelated pairs like WETH/USDC.

By borrowing one side of the pair and supplying the other, LPs can offset directional exposure. These strategies can be managed manually or automated through operator contracts.

Custom AMM curves and operator control
EulerSwap supports custom AMM curves defined at pool creation. These curves can be:

Symmetric or asymmetric
Single-sided or concentrated
Designed for volatility or range-bound markets
LPs can update curve parameters via smart contract operators. This enables liquidity programs that adapt over time or respond to external inputs.

Each pool is owned and controlled by a single LP
Unlike traditional AMMs, EulerSwap does not use shared liquidity pools. By default, each EulerSwap instance is created and managed by a single LP account. This design gives LPs:

Full control over the pool’s AMM curve
Customisable pricing, spreads, and liquidity profiles
Integrated access to leverage and collateral strategies
This architecture is ideal for DAOs, token teams, and sophisticated market makers who want to manage liquidity provision as an active strategy.

Uniswap v4 compatibility
EulerSwap is built to be fully compatible with Uniswap v4’s hook architecture. This means it can plug into Uniswap’s routing and solver networks while extending functionality with lending-based logic.

Users can interact with EulerSwap through standard swap interfaces, unaware that beneath the surface, borrowing, lending, and advanced execution logic are taking place.

Who it's for
EulerSwap is built for:

Token issuers who want to bootstrap liquidity without mercenary incentives
DAOs seeking to improve the capital efficiency of protocol-owned liquidity
Market makers pursuing efficient, hedgeable LP positions
Sophisticated DeFi users looking to combine lending and swaps in their trading strategies
Example use cases for EulerSwap
Stableswap-style pool for correlated assets
Create a pool between two closely correlated stablecoins and earn both swap fees and boosted yield by lending the assets. You can borrow against the entire LP position to hedge risk or increase the effective liquidity depth via just-in-time liquidity.

Example:

Supply USDT/USDtb liquidity and either:borrow USDC against the position, or
Enable JIT liquidity to provide greater depth of liquidity for swaps.
Uniswap v2-style pool for uncorrelated long-tail assets
Create a traditional 50/50 pool between a long-tail token and a stablecoin. Earn swap fees and potentially boosted lending yield from the quote asset, and optionally from the base asset if it is lendable.

Example: Supply UNI/USDC liquidity. Earn yield on USDC and, if supported, on UNI as well.

Dynamically hedged pool for uncorrelated majors
Set up a pool between volatile assets and hedge exposure to impermanent loss by borrowing one asset against the other. Adjust the loan automatically to maintain a delta-neutral or targeted risk profile, while earning swap fees and lending yield on both assets.

Example: Supply USDC, borrow ETH, create a USDC/WETH pool, and dynamically hedge by adjusting the ETH loan in response to price movements.

Launchpad-style pool with asymmetric liquidity
Deploy a pool with concentrated liquidity on one side (e.g., the token being launched) and distributed liquidity on the other. This allows fixed-price execution for initial buyers while enabling price discovery on the opposing side.

Example: Provide concentrated liquidity in a new token against a stablecoin to facilitate early-stage swaps and bootstrap price formation.

Learn more
If you're a token issuer, LP, or DeFi builder interested in getting involved, we invite you to:

Read the full white paper
Join the Discord server and turn notifications on to be updated when it’s live!
We're also launching a builder competition to celebrate EulerSwap's release. Participants will have four weeks to build something great on top of the new protocol.

🥇 First prize: $25,000 in rEUL
🥈 Second prize: $10,000 in rEUL
🥉 Third prize (3 teams): $5,000 in rEUL each
Whether you're creating strategies, tools, or integrations, we’re excited to see what you’ll build!

The competition will be announced in the near future, with full details to be shared in the Discord.

Security
EulerSwap has undergone extensive security review, with five leading audit firms involved and independent researchers engaged from the early stages of development.

A custom fuzzing campaign led by Victor Martinez (aka Enigma Dark) has been running continuously since January, using tools like Echidna and Foundry (Forge) to identify edge-case bugs and rigorously test the AMM’s invariants.

To further harden the system, a $500,000 capture-the-flag competition will soon be launched, inviting security researchers to battle-test the code in a live setting. EulerSwap is also covered by Euler’s Bug Bounty programme in partnership with Cantina, offering additional incentives for vulnerability discovery.

Importantly, EulerSwap is built on top of Euler’s lending infrastructure. By using native vaults for capital management, it inherits many of Euler’s underlying safety properties. At the time of writing, the Euler protocol and its modules have collectively undergone over 40 independent audits.
