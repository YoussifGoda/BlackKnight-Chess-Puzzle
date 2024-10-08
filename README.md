# Black Knight Puzzle Game
<img width="798" alt="Screenshot 2024-09-26 at 2 18 42 PM" src="https://github.com/user-attachments/assets/0687887a-bbc7-4af9-8423-cedc25594d5f">

## Description

Black Knight Puzzle is a chess-inspired puzzle game implemented in Python using the Pygame library. The objective is to move the black knight to a specific target square on a custom chess board while navigating around other pieces.

## Features

- Custom 6x2 chess board with two additional squares
- Movement of white pieces (bishops, knights, rooks) and a single black knight
- No turn order - players can move any piece at any time
- Win condition when the black knight reaches the target square

## Requirements

- Python 3.7+
- Pygame 2.0.1+

## Installation

1. Ensure you have Python installed on your system. You can download it from [python.org](https://www.python.org/downloads/).

2. Install Pygame by running the following command in your terminal:
   ```
   pip install pygame
   ```

3. Clone this repository or download the source code:
   ```
   git clone https://github.com/YoussifGoda/black-knight-puzzle.git
   cd black-knight-puzzle
   ```

## File Structure

Ensure your project directory looks like this:

```
black-knight-puzzle/
│
├── black_knight_puzzle.py
├── assets/
│   └── images/
│       ├── black knight.png
│       ├── white bishop.png
│       ├── white knight.png
│       └── white rook.png
├── NightPumpkind-1GpGv.ttf
├── Blacknorthdemo-mLE25.ttf
└── README.md
```

## Running the Game

1. Navigate to the game directory in your terminal.

2. Run the following command:
   ```
   python black_knight_puzzle.py
   ```

## How to Play

1. The game board will appear with white pieces (bishops, knights, rooks) and a single black knight.

2. Click on any piece to select it. Valid moves will be highlighted with red circles.

3. Click on a highlighted square to move the selected piece.

4. There is no turn order - you can move any piece (white or black) at any time.

5. The goal is to move the black knight to the light blue square in the top-right corner of the board.

6. The game ends when the black knight reaches the target square.

## Controls

- Left Mouse Button: Select and move pieces

## Customization

You can customize the game by modifying the following in `black_knight_puzzle.py`:

- Board size and layout
- Initial piece positions
- Piece images
- Font styles

## Troubleshooting

If you encounter any issues:

1. Ensure all required files (images, fonts) are in the correct directories.
2. Verify that Pygame is installed correctly.
3. Check that you're using a compatible Python version.

## Contributing

Feel free to fork this repository and submit pull requests with improvements or bug fixes.

## License

This project is open source and available under the [MIT License](https://opensource.org/licenses/MIT).
