import json
import os
import shutil
import sys
import requests
#from Chess import Board, Piece
import tqdm
import chess
import stockfish
import chess.engine

CURRENTFEN: str
ISWHITE: bool

SESSION = requests.Session()

def get_games(player):
    """Get all games of a player."""
    player = player.lower()
    
    url = f"https://api.chess.com/pub/player/{player}/games/archives"
    #print(url)
    headers = {"User-Agent": "Python Robot :)", "From": "will.v.garrison@gmail.com"}
    
    SESSION.headers.update(headers)
    print(SESSION.headers)
    response = SESSION.get(url)
    print(response.headers)
    if response.status_code != 200:
        print(f"Error: {response.status_code}, error while loading profile")
        sys.exit(1)
    return response.json()["archives"]






def movesToFenList(moves, startFen):
    fenList = []
    board = chess.Board(startFen)
    for x in moves:
        try:
            board.push_san(x)
            fenList.append(board.fen())
        except:
            
            continue
    return fenList

def parse_pgn(pgn):
    """Parse a PGN file."""
    pgn = pgn.split("\n\n")
    headers = pgn[0].split("\n")
    headers = [header.split(" ", 1) for header in headers]
    headers = {header[0][1:]: header[1][1:-2] for header in headers}
    pgnMoves = pgn[1].split(" ")
    moves = []
    for x in range(len(pgnMoves)):
        if x%4==1:
            moves.append(pgnMoves[x])
    #print("Headers: ", headers)
    moves=movesToFenList(moves, headers["StartFen"])
    #print("Moves: ", moves)
    return moves




def checkNumberOfGames(games):
    num = 0
    for url in games:
        x = SESSION.get(url).json()
        game=x["games"]
        num+=len(game)
    return num


def downloadGames(games, num):
    if os.path.exists("TrainingData"):
        shutil.rmtree("TrainingData")
    os.mkdir("TrainingData")
    os.mkdir("TrainingData/Games")
    bar=tqdm.tqdm(total=num)
    for url in games:
        
        tqdm.tqdm.write(f"Downloading Game {url}")
        # User agent with contact info
        headers = {"User-Agent": "Python Robot :)", "From": "will.v.garrison@gmail.com"}
        SESSION.headers.update(headers)
        game = SESSION.get(url)
        if game.status_code != 200:
            tqdm.tqdm.set_description(f"Error: {game.status_code}")
            continue
        game = game.json()
        for x in game["games"]:
            try:
                
                bar.set_description(f"Downloading Game {x['url']}",refresh=True)
                bar.update(1)
                pgn = x["pgn"]
                pgn = f'[StartFen "{x["initial_setup"]}"]\n' + pgn
                pheaders = pgn.split("\n\n")
                pheaders = pheaders[0].split("\n")
                pheaders = [pheader.split(" ", 1) for pheader in pheaders]
                pheaders = {pheader[0][1:]: pheader[1][1:-2] for pheader in pheaders}
                name = f"{pheaders['White']} vs {pheaders['Black']}"
                if os.path.exists(f"TrainingData/Games/{name}.pgn"):
                    name+="000001"
                while os.path.exists(f"TrainingData/Games/{name}.pgn"):
                    name = name[:-6] + str(int(name[-6:])+1).zfill(6)
                
                open(f"TrainingData/Games/{name}.pgn", "w").write(pgn)
            except KeyError:
                tqdm.tqdm.write("KeyError")
                continue
            
    bar.close()
    

def stockfishEvaluate(fenList):
    engine = chess.engine.SimpleEngine.popen_uci("C:\\Users\\WVGarrison\\Documents\\Python\\ChessAi\\stockfish\\stockfish-windows-x86-64-avx2.exe")
    board = chess.Board(chess.STARTING_FEN)
    info = engine.analyse(board, chess.engine.Limit(depth=20,time=0.01))
    #print(info["score"], info["score"].pov(chess.WHITE), info["nodes"], info["time"])
    fenDict = {}
    for fen in fenList:
        board = chess.Board(fen)
        info = engine.analyse(board, chess.engine.Limit(depth=20,time=0.01))
        if info["score"].pov(chess.WHITE).is_mate():
            # Check mate in x
            x = info["score"].pov(chess.WHITE).mate()
            if x >= 0:
                fenDict[fen] = 1000000000
            else:
                fenDict[fen] = -1000000000
        else:
            fenDict[fen] = info["score"].pov(chess.WHITE).score()/100
    engine.close()
    return fenDict

def createDataSet():
    if not os.path.exists("TrainingData"):
        raise FileNotFoundError("TrainingData folder not found.")
    if os.path.exists("TrainingData/TrainingGames"):
        shutil.rmtree("TrainingData/TrainingGames")
        
    os.mkdir("TrainingData/TrainingGames")
    
    loadingBar=tqdm.tqdm(total=len(os.listdir("TrainingData/Games")),desc="Creating Training Data")
    dataSetFile = open("TrainingData/TrainingGames/dataSet.json", "a")
    dataSetFile.write('{"dataset" : {\n')
    for x in os.listdir("TrainingData/Games")[:10]:
        fenList = parse_pgn(open(f"TrainingData/Games/{x}").read())
        if fenList == []:
            continue
        fenDict = stockfishEvaluate(fenList)
        # Add to dataset file
        dataSetFile.write(f'"{x}" : '+json.dumps(fenDict))
        if x != os.listdir("TrainingData/Games")[9]:
            dataSetFile.write(",\n")
        loadingBar.update(1)
        loadingBar.set_description(f"Creating Training Data: {x}")
    dataSetFile.write("}}")
    dataSetFile.close()
    
    

while True:
    try:
        player = input("Enter a player: ")
        if not player:
            break
        games = get_games(player)
        if not games:
            print("No games found.")
            continue
        print("loading profile...")
        num =50625# checkNumberOfGames(games)
        print(f"Found {num} games.")
        confirm = input("Download games Y/N: ")
        if confirm.lower() == "y":
            #downloadGames(games, num)
            createDataSet()
    except KeyboardInterrupt:
        break
