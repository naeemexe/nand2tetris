# Project 7 — VM I: stack arithmetic & memory access

The translator lives in [`../8/vm_translator.py`](../8/vm_translator.py): project 8
extends the same program with branching and function calls, so there is one file
instead of two copies that drift apart.

```bash
python3 ../8/vm_translator.py StackArithmetic/SimpleAdd/SimpleAdd.vm
../../tools/CPUEmulator.sh StackArithmetic/SimpleAdd/SimpleAdd.tst
```

What project 7 covers inside that file: `write_push`, `write_pop`, `write_arithmetic`
and the shared `$$EQ/$$GT/$$LT` routines. See `notes/04-vm-translator.md`.
