# `Linux`

<h2>Table of contents</h2>

- [What is `Linux`](#what-is-linux)
- [User](#user)
  - [The user `root`](#the-user-root)
  - [A non-root user](#a-non-root-user)
- [Group](#group)
  - [`sudo` group](#sudo-group)
- [Permissions](#permissions)
  - [Owner](#owner)
  - [Mode](#mode)
    - [Common modes](#common-modes)

## What is `Linux`

`Linux` is a family of [operating systems](./operating-system.md) commonly used for servers and [virtual machines](./vm.md).

See:

- [`Linux` distros](./linux-distros.md#what-is-a-linux-distro).
- [`Linux` administration](./linux-administration.md#what-is-linux-administration).

## User

See [User](./operating-system.md#user).

### The user `root`

`root` is the administrator [user](#user).

### A non-root user

A non-root user is a regular [user](#user) account without administrator privileges.

Non-root users can only access [files](./file-system.md#file) and run [programs](./software-types.md#program) that their [permissions](#permissions) allow.
To perform administrative actions, a non-root user must use the [`sudo` command](./linux-administration.md#the-sudo-command).

## Group

See [Group](./operating-system.md#group).

### `sudo` group

The `sudo` [group](#group) is a special group on `Ubuntu`/`Debian` systems whose members are allowed to run commands with elevated [permissions](#permissions) using the [`sudo` command](./linux-administration.md#the-sudo-command).

Adding a [user](#user) to the `sudo` group grants them administrator access without using [the user `root`](#the-user-root) directly.

## Permissions

On [`Linux`](#what-is-linux), each [file](./file-system.md#file) and [directory](./file-system.md#directory) has [permissions](./operating-system.md#permission) that control access for three categories:

- the [owner](#owner) user
- the owner [group](#group)
- everyone else

Each category can have three types of access:

- **Read (`r`)** — view the contents of a file or list the contents of a directory.
- **Write (`w`)** — modify a file or add/remove files in a directory.
- **Execute (`x`)** — run a file as a program or enter a directory.

See:

- [Change permissions](./linux-administration.md#change-permissions).

### Owner

Every [file](./file-system.md#file) and [directory](./file-system.md#directory) has an owning [user](./operating-system.md#user) and an owning [group](./operating-system.md#group). The owner determines which category of the [mode](#mode) applies to a given user.

See:

- [`chown`](./linux-administration.md#chown) — change the owner and group.

### Mode

A mode is a three-digit number (e.g., `755`, `600`) that encodes the read, write, and execute [permissions](#permissions) for the [owner](#owner) user, the owner group, and everyone else respectively.

#### Common modes

- `700` — owner can read, write, and execute; no access for group or others.
- `600` — owner can read and write; no access for group or others.
- `644` — owner can read and write; group and others can read.
