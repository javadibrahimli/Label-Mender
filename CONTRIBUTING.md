# Contributing to Label Mender

First off, thank you for considering contributing to Label Mender! 

This is a basic tool created for labelers who work with YOLO annotations. Every contribution helps make this tool better for the community.

## Ways to Contribute

### Reporting Bugs

Found a bug? Please open an issue with:
- A clear title and description
- Steps to reproduce the issue
- Expected vs actual behavior
- Screenshots if applicable
- Your OS and Python version

### Suggesting Features

Have an idea? Open an issue with:
- A clear description of the feature
- Why it would be useful for labelers
- Any examples or mockups if applicable

### Code Contributions

1. **Fork** the repository
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Label-Mender.git
   cd Label-Mender
   ```
3. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Make your changes** and test them
6. **Commit** with a clear message:
   ```bash
   git commit -m "Add: brief description of your changes"
   ```
7. **Push** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
8. **Open a Pull Request**

## Code Style Guidelines

- Follow PEP 8 conventions
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small
- Add type hints where possible

## Project Structure

```
Label-Mender/
├── app.py                  # Entry point
├── src/
│   ├── config/             # Configuration and styling
│   ├── core/               # Business logic (managers)
│   ├── ui/                 # User interface components
│   └── utils/              # Utility functions
```

## Commit Message Format

Use clear, descriptive commit messages:
- `Add: new feature description`
- `Fix: bug description`
- `Update: what was changed`
- `Remove: what was removed`
- `Refactor: what was refactored`

## Questions?

Feel free to open an issue if you have any questions. We're happy to help!

---

Thank you for contributing! 
