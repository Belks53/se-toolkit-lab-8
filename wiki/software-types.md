# Software types

<h2>Table of contents</h2>

- [What is software](#what-is-software)
- [Source code](#source-code)
- [Program](#program)
- [Library](#library)
  - [Shared library](#shared-library)
- [Executable](#executable)

## What is software

Software is a set of instructions that tells a computer what to do.

Software comes in different forms depending on how it is used — for example, as an executable program, a reusable library, or a web application.

How software may be used, copied, and shared is governed by its [distribution terms](./software-distribution.md#about-software-distribution).

## Source code

Source code is the human-readable text written by programmers that defines how [software](#what-is-software) behaves. It is written in a programming language (e.g., `Python`, `JavaScript`) and must be translated into machine instructions before a computer can run it.

## Program

A program is [software](#what-is-software) designed to be run directly to perform a specific task.

It is built from [source code](#source-code), may depend on [libraries](#library), and is distributed as an [executable](#executable).

When launched, the program becomes a [process](./operating-system.md#process) managed by the [operating system](./operating-system.md#what-is-an-operating-system).

## Library

A library is reusable [software](#what-is-software) that provides functionality other programs can use without reimplementing it themselves.
Libraries are not run directly — they are loaded by a program at startup or during execution.

### Shared library

A shared library is a library stored as a separate file (e.g., `libatomic.so.1` on [`Linux`](./operating-system.md#linux)) and loaded at [runtime](./program-lifecycle.md#runtime) by one or more [programs](#program).

If a required shared library is missing from the system, the program will fail to start.

## Executable

An executable is a file that contains machine instructions that the [operating system](./operating-system.md#what-is-an-operating-system) can run directly.

It is the end product of compiling [source code](#source-code) — for example, `python3` on [`Linux`](./operating-system.md#linux) or `notepad.exe` on [`Windows`](./operating-system.md#windows).

When run, the executable becomes a [process](./operating-system.md#process).
