# Snake (project 9)

My own Jack program: classic Snake on the Hack screen.

| File | What it does |
|---|---|
| `Random.jack` | 16-bit linear congruential generator, seeded by how long you wait on the title screen |
| `Snake.jack` | the body as a ring buffer of cells: one move = push a head + drop the tail, both O(1) |
| `SnakeGame.jack` | 64x30 grid of 8x8 cells, occupancy grid for O(1) collision checks, game loop |
| `Main.jack` | title screen, seeding, start/stop |

Run it:

```bash
python3 ../../11/jack_compiler.py .   # or: tools/JackCompiler.sh projects/9/Snake
```

then load the folder in the VM Emulator (with the OS .vm files, or its built-in OS),
pick *No animation*, and use the arrow keys. `Q` quits.
