# Connect 4 AI: Minimax & MCTS Solvers

## 📌 Overview
This repository contains two AI implementations for playing Connect 4:
1. **Minimax Algorithm** with alpha-beta pruning and extensive optimizations
2. **Monte Carlo Tree Search (MCTS)** implementation with UCT selection

## 💻 Optimizations
### Minimax
- **Alpha-beta pruning**: Eliminates unnecessary searching branches where a better move is guaranteed to not appear
- **Bitboard representation**: Makes checking wins extremely fast (no looping/iteration) while reducing memory usage
- **Transposition tables**: Stores previously evaluated positions to avoid redundant computation
- **Iterative deepening**: To gauge what depth can be searched while staying under the time limit
- **Sliding window evaluation**: To reduce redundant computation when checking for connected pieces
- **Center-column move ordering**: Searches the center column first as many Connect 4 strategies promote center control

| Optimization          | Benefit                          | Speedup Factor |
|-----------------------|----------------------------------|----------------|
| Alpha-beta pruning    | Prevents suboptimal branch checking | ~50x        |
| Bitboards             | O(1) win detection, less memory usage| ~50x       |
| Transposition tables  | Avoids redundant evaluations    | ~8x             |
| Sliding window eval   | Fast pattern scoring            | ~3x             |
| Pragma compiler flags | Hardware-based optimization     | ~1.5x

**Overall Improvement**: ~100,000x, check comments in minimax.c++

### Monte Carlo Tree Search
- **UCT selection policy**: To determine whether to explore new positions or exploit existing positions, with the theoretical optimal value of $\sqrt{2}$ as the constant of exploration
- **Bitboard representation**: Same reason as minimax

## 🎓 Technical Insights
- **Constant-factor/average-case Optimization**: Many optimizations (such as using bitboards and alpha-beta pruning) do not decrease the big-O worst-case time complexity (the Connect 4 board is of a fixed size in the case of bitboards), but offer large speedups empirically. This is through reducing the average-case time complexity, which is usually more important in these scenarios.
- **Modular Programming**: Functions and classes are used (check minimax.c++ and montecarlo.c++) to reduce clutter and improve readability.
- **Randomness**: Non-deterministic algorithms, such as MCTS, may sometimes outperform and offer more benefits than deterministic algorithms such as minimax. For example, MCTS allows precise allocation of time per move, while minimax can only offer a "recommendation". Furthermore, after testing, MCTS consistently beats minimax when given 10 seconds for each move, regardless of first-move advantage.

## 🔍 Future Work
- **Parallelization**: Multiple cores can run MCTS simulations or minimax tree searching concurrently, which may offer large performance increases. However, it is difficult to allocate threads and manage read/write operations without losing efficiency, especially in the case of minimax, because the number of cores in a machine may not be exact multiples of 7 (for 7 columns), causing some cores to be under-utilized.
- **Benchmarking**: Standard implementations of minimax and MCTS, or other strategies, can play games against my implementations. Win rates and move times can be evaluated.
- **Hybrid Approach**: Positions which require subtle lines of play may be better suited for minimax as MCTS sometimes fails to detect them. Using both may improve performance and quality of play.
- **Neural Networks**: Neural networks may be used in the evaluation function at shallower depths in the minimax algorithm to determine whether a side is heavily likely to win in order to prune branches earlier. They offer more nuance than evluation functions, which are designed by hand, potentially lacking some key scoring details that is cruicial for some positions.

## 🚀 Build and Run
1. Make a copy of this repo
2. Navigate to the scripts directory:
```bash
cd scripts
```
3. Compile and run the Connect 4 game using different algorithms
```bash
g++ minimax.c++ -o minimax.exe
```
then 
```bash
./minimax.exe
```
or
```bash
g++ minimax.c++ -o minimax.exe
```
then
```bash
python gui.py
```
### Dependencies

#### System Requirements
- Windows/Linux/macOS

#### Environment Requirements
- Python 3.12+
- Pygame package
- GCC 12+ (`-std=c++23`)
- CMake 3.15+ (optional, for building from source)

## 📖 References and Resources
- Monte Carlo Tree Search, Wikipedia. https://en.wikipedia.org/wiki/Monte_Carlo_tree_search
- Minimax, Wikipedia. https://en.wikipedia.org/wiki/Minimax
- Alpha-beta pruning, Wikipedia. https://en.wikipedia.org/wiki/Alpha%E2%80%93beta_pruning
- Browne, Cameron. (2014). Bitboard Methods for Games. ICGA journal. 37. 67-84. [10.3233/ICG-2014-37202](https://www.researchgate.net/publication/279031895_Bitboard_Methods_for_Games/citations).
- Wächter, L. (2021, December 23). Improving Minimax performance. DEV Community. https://dev.to/larswaechter/improving-minimax-performance-1924
