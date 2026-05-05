# envault

> Lightweight local secrets manager that encrypts `.env` files using a master passphrase.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/) for isolated installs:

```bash
pipx install envault
```

---

## Usage

**Encrypt an existing `.env` file:**

```bash
envault lock .env
# Enter master passphrase: ••••••••
# ✔ Encrypted → .env.vault
```

**Decrypt and load secrets into your shell session:**

```bash
envault unlock .env.vault
# Enter master passphrase: ••••••••
# ✔ Secrets loaded into environment
```

**Use directly in Python:**

```python
import envault

envault.load(".env.vault", passphrase="my-secret-phrase")

import os
print(os.getenv("DATABASE_URL"))
```

> **Tip:** Never commit `.env` to version control. You can safely commit `.env.vault` instead.

---

## How It Works

envault uses AES-256-GCM encryption with a key derived from your master passphrase via PBKDF2-HMAC-SHA256. No secrets are stored in plaintext on disk.

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

---

## License

[MIT](LICENSE) © 2024 envault contributors