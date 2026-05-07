# Passphrase Rotation

The `rotate` command lets you re-encrypt a locked vault under a new master
passphrase without ever leaving secrets on disk in plaintext longer than
necessary.

## Usage

```bash
envault rotate [--env .env] [--vault .env.vault] OLD_PASSPHRASE NEW_PASSPHRASE
```

### Arguments

| Argument | Default | Description |
|---|---|---|
| `old_passphrase` | *(required)* | Current master passphrase |
| `new_passphrase` | *(required)* | Replacement master passphrase |
| `--env` | `.env` | Path to the plaintext env file |
| `--vault` | `.env.vault` | Path to the encrypted vault file |

## How it works

1. Verifies the vault file exists and the env file is **absent** (i.e. the
   vault is in the locked state).
2. Decrypts the vault with `old_passphrase`, writing the plaintext to
   `--env`.
3. Re-encrypts the plaintext with `new_passphrase`, overwriting the vault
   file.
4. Records a `rotate` event in the audit log.

## Example

```bash
# Lock your secrets first if not already locked
envault lock mysecretpass

# Rotate to a new passphrase
envault rotate mysecretpass mynewsecretpass

# Verify the vault is still locked
envault status
# locked
```

## Errors

- **Vault file not found** — the `.env.vault` file does not exist yet.
- **Vault must be locked** — the plaintext `.env` is still present; run
  `envault lock` first.
- **Failed to decrypt** — the `old_passphrase` is incorrect.
