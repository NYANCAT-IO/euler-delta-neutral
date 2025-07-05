# Claude Development Guidelines

## Project Context

This is a delta-neutral LP backtesting project for EulerSwap, built using Anaconda and Jupyter notebooks. The project is designed for hackathon demonstration and educational purposes, with clear disclaimers about overfitting and limitations for live trading.

## Core Development Principles

### 1. Always Commit Changes
- **ALWAYS** commit your changes with descriptive commit messages
- **Never** leave uncommitted work at the end of a session
- Commit frequently with logical, atomic changes
- Use conventional commit format: `type: description`

### 2. Pre-Commit Security Checklist

Before **EVERY** commit, you **MUST** check for:

#### Sensitive Data (CRITICAL)
- [ ] No API keys, passwords, or tokens in any files
- [ ] No personal information or email addresses
- [ ] No database credentials or connection strings
- [ ] No private keys or certificates
- [ ] Check all .env files are properly gitignored

#### Environment Files
- [ ] No .env files committed (should be in .gitignore)
- [ ] No conda environment files with absolute paths
- [ ] No IDE-specific configuration files

#### Data Files (Performance)
- [ ] No large datasets committed (>100MB files)
- [ ] No raw data files in data/ directories
- [ ] No generated reports or plots in results/
- [ ] No cache files or temporary directories

#### Dependencies
- [ ] No node_modules/ or __pycache__/ directories
- [ ] No .conda/ or venv/ environment directories
- [ ] No compiled binaries or build artifacts
- [ ] No IDE temporary files (.vscode/, .idea/, etc.)

### 3. Commit Message Guidelines

Use this format for all commits:
```
type(scope): brief description

Longer explanation if needed

- Include bullet points for complex changes
- Reference issue numbers when applicable
```

**Types:**
- `feat`: New features or major functionality
- `fix`: Bug fixes and corrections
- `docs`: Documentation updates
- `style`: Code style changes (no logic changes)
- `refactor`: Code restructuring without changing behavior
- `test`: Adding or updating tests
- `chore`: Maintenance, dependencies, tooling

**Examples:**
```
feat(strategy): implement delta-neutral rebalancing logic

- Add core delta calculation functions
- Implement hedge ratio optimization
- Include transaction cost modeling

docs(architecture): add technical architecture documentation

chore(env): update gitignore for Anaconda and data files
```

### 4. Development Workflow

#### When Starting Work
1. Check current branch and pull latest changes
2. Review existing todos and documentation
3. Create/update todos for planned work
4. Activate correct conda environment

#### During Development
1. Write code in small, logical chunks
2. Test changes frequently in Jupyter notebooks
3. Update documentation as you go
4. Add comments for complex logic

#### Before Committing
1. **RUN THE SECURITY CHECKLIST ABOVE**
2. Review all changed files for sensitive data
3. Test that code runs without errors
4. Update relevant documentation
5. Create descriptive commit message

### 5. Anaconda Environment Management

#### Environment Activation
```bash
# Always activate the project environment
conda activate euler-backtest
```

#### Adding Dependencies
```bash
# For conda packages (preferred)
conda install -c conda-forge package_name

# For pip packages (when conda unavailable)
pip install package_name

# Update environment.yml after major changes
conda env export > environment.yml
```

#### Environment File Guidelines
- Keep environment.yml clean and minimal
- Don't include development-only dependencies in production environment
- Use version pinning for critical packages
- Test environment recreation regularly

### 6. File Organization Standards

#### Jupyter Notebooks
- Use clear, descriptive names with numbers for ordering
- Include markdown cells explaining each section
- Clear all outputs before committing (except final results)
- Keep notebooks focused on single topics

#### Python Modules
- Follow PEP 8 style guidelines
- Include comprehensive docstrings
- Use type hints for function signatures
- Organize imports (standard library, third-party, local)

#### Documentation
- Update relevant docs when changing functionality
- Use consistent markdown formatting
- Include code examples in documentation
- Keep README.md updated with setup instructions

### 7. Data Management Rules

#### Never Commit:
- Raw datasets from subgraphs
- Processed data files (use Parquet compression)
- Optimization results and cached computations
- Generated plots and reports
- Personal API keys or credentials

#### Always Include:
- Sample data for testing (small, anonymized)
- Data schema documentation
- Example configuration files
- Instructions for data acquisition

### 8. Security Best Practices

#### Environment Variables
```python
# Always use environment variables for sensitive data
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('THEGRAPH_API_KEY')
if not API_KEY:
    raise ValueError("Missing required API key")
```

#### API Key Management
- Store in .env file (gitignored)
- Never hardcode in source files
- Use descriptive environment variable names
- Include .env.example with dummy values

#### Data Privacy
- Anonymize any user addresses or personal data
- Use aggregated data when possible
- Avoid logging sensitive information
- Implement data retention policies

### 9. Testing and Validation

#### Code Quality Tools Available
- **Ruff v0.8.2**: Ultra-fast Python linter and formatter (Rust-based, 10-100x faster)
- **Black v24.8.0**: The uncompromising Python code formatter
- **Python AST**: Built-in syntax validation

#### Before Committing (MANDATORY)
```bash
# 1. Fast syntax validation
python -m py_compile src/**/*.py

# 2. Code formatting and linting (REQUIRED)
ruff format .                    # Format all Python code
ruff check --fix .              # Fix auto-fixable issues

# 3. Final validation
ruff check .                    # Ensure no remaining issues

# 4. Notebook execution test
jupyter nbconvert --execute notebooks/*.ipynb --to python

# 5. Check for incomplete work
grep -r "TODO" . --exclude-dir=.git
grep -r "FIXME" . --exclude-dir=.git

# 6. Verify all checks pass
echo "✅ All validation completed successfully"
```

#### Ruff Configuration (ruff.toml)
```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings  
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (black handles this)
    "B008", # function calls in argument defaults
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

#### Performance Comparison
- **Ruff**: ~0.5s for entire project (format + lint)
- **Black**: ~2-5s for entire project (format only)
- **Traditional tools**: 30-60s for full validation

#### Alternative: Black Formatting
```bash
# If you prefer Black's formatting style
black .                         # Format code
black --diff .                  # Preview changes
```

#### Data Validation
- Always validate data shapes and types
- Check for missing or corrupted data
- Verify data quality metrics
- Include data lineage documentation

### 10. Error Handling

#### Robust Code Patterns
```python
# Always include error handling for external APIs
try:
    data = fetch_subgraph_data(query)
except requests.RequestException as e:
    logger.error(f"Failed to fetch data: {e}")
    raise

# Validate data before processing
if data.empty:
    raise ValueError("No data available for processing")
```

#### Logging Best Practices
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.info("Starting data processing")
logger.warning("Low data quality detected")
logger.error("Critical error in calculation")
```

### 11. Session Management

#### At Session Start
1. Pull latest changes from git
2. Activate conda environment
3. Review todo list and current progress
4. Check for any environment issues

#### During Session
1. Commit frequently with descriptive messages
2. Update todos as work progresses
3. Document any issues or discoveries
4. Keep workspace clean and organized

#### At Session End
1. **CRITICAL**: Run complete security checklist
2. Commit all changes with final summary
3. Update project status in README
4. Clean up temporary files
5. Provide clear handoff notes

### 12. Project-Specific Guidelines

#### EulerSwap Integration
- Always test subgraph queries before using in production
- Include rate limiting for API calls
- Handle network timeouts gracefully
- Validate all financial calculations

#### Backtesting Standards
- Use consistent random seeds for reproducibility
- Include transaction costs in all calculations
- Test strategies on multiple time periods
- Document all assumptions clearly

#### Overfitting Warnings
- Include prominent disclaimers in all results
- Show parameter sensitivity analysis
- Demonstrate out-of-sample performance degradation
- Clearly separate educational from investment content

## Emergency Procedures

### If You Accidentally Commit Sensitive Data
1. **DO NOT PUSH** to remote repository
2. Use `git reset --soft HEAD~1` to uncommit
3. Remove sensitive files and add to .gitignore
4. Re-commit with clean files
5. If already pushed, contact repository owner immediately

### If Environment Breaks
1. Export current package list: `conda list --export > backup_packages.txt`
2. Try recreating: `conda env create -f environment.yml`
3. If that fails, start fresh and reinstall packages manually
4. Update environment.yml once working

Remember: This project is for educational demonstration. Always prioritize security, documentation, and reproducibility over speed of development.