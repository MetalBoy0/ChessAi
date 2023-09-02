from torch import nn, save, load, tensor, float32,long
from torch import optim
from torch.utils import data
import torch.nn.functional as F
import json
import net
import tqdm


def toBoard(fen):
    # fen is a string of the board
    # returns a 1d array of the board
    board = []
    pieceIDs = {"p": 1, "n": 2, "b": 3, "r": 4, "q": 5, "k": 6, "P": 7, "N": 8, "B": 9, "R": 10, "Q": 11, "K": 12}
    fen = fen.split(" ")
    fenPos = fen[0]
    sideToMove = fen[1]
    for x in fenPos:
        if x == "/":
            continue
        elif x.isnumeric():
            for i in range(int(x)):
                board.append(0)
        else:
            board.append(pieceIDs[x])
    # Append the side to move
    if sideToMove == "w":
        board.append(1)
    else:
        board.append(-1)
    
    return tensor(board)



class Dataset(data.Dataset):
    def __init__(self, fens, evals):
        # Convert to 1d array fen (game (Fen1, fen2,), game(fen1, fen2)))
        fens = [y for x in fens for y in x]
        evals = [y for x in evals for y in x]
        self.fens = fens
        self.evals = evals
    def __len__(self):
        return len(self.fens)
    def __getitem__(self, index):
        fen = self.fens[index]
        _eval = self.evals[index]
        fen = toBoard(fen)
        
        
        
        return fen, _eval


def loadDataSet(jsonFile):
    print("Opening json file...")
    file = open(jsonFile, "r")
    data = json.load(file)
    print("file loaded, processing data...")
    games = data["dataset"]
    # games is formatted as a dict, with the name of the game as the key, and the value as a dict of fen:eval
    games = list(games.items())
    evals = []
    fen = []
    # gamesDictList = [{fen:eval, fen:eval, fen:eval}, {fen:eval, fen:eval, fen:eval}, {fen:eval, fen:eval, fen:eval}]
    
    for i in tqdm.trange(len(games), desc="Processing data"):
        x=games[i][1]
        evals.append(list(x.values()))
        fen.append(list(x.keys()))
    return Dataset(fen, evals)

def main(chessData):
    
    loader = data.DataLoader(chessData, batch_size=1, shuffle=True)
    
    model = net.Module()
    
    optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.9)
    criterion = nn.MSELoss()
    
    epochs = 10
    model.train()
    for epoch in range(epochs):
        print("Epoch: ", epoch)
        bar = tqdm.tqdm(len(loader), desc="Epoch: " + str(epoch))
        for i, (inputs, labels) in enumerate(loader):
            
            bar.update(1)
            optimizer.zero_grad()
            output = model(inputs.to(float32))
            loss = criterion(output, labels).to(float32)
            loss.backward()
            optimizer.step()
        else:
            print("Loss: ", loss.item())
    bar.close()
    save(model.state_dict(), "model.pth")



if __name__ == "__main__":
    chessData = loadDataSet("C:\\Users\\WVGarrison\\Documents\\Python\\ChessAi\\TrainingData\\TrainingGames\\dataSet.json")
    main(chessData)

