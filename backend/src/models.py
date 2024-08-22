#!/usr/bin/python3
"""
Contains the models of the application.
"""
import string
import random
from datetime import datetime

from src import db


class BaseModel():
    """Base class for other models"""
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(), default=datetime.utcnow)

    def to_dict(self):
        return self.__dict__

class GamePlayerAssociation(db.Model):
    """Association table between players and games"""
    __tablename__ = "game_players"
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), primary_key=True, nullable=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), primary_key=True)
    player = db.relationship("Player", backref="played_games")
    game = db.relationship("Game", backref="game_players")


class Player(db.Model, BaseModel):
    """Model for the game players"""
    __tablename__ = "players"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(25), nullable=False)
    playing = db.Column(db.Boolean, default=False) # This would come in handy if we choose to prohibit a user playing multiple games simultaneously
    score = db.Column(db.Integer, default=0)
    moves = db.relationship("Move", backref="moving_player")
    messages = db.relationship("Message", backref="messaging_player")

    def create_game(self, difficulty):
        """Creates a new game of given difficulty and returns the instance"""
        new_game = Game()
        new_game.difficulty = difficulty
        db.session.add(new_game)
        db.session.commit()

        gp_assoc = GamePlayerAssociation()
        gp_assoc.player_id = self.id
        gp_assoc.game_id = new_game.id
        db.session.add(gp_assoc)
        db.session.commit()

        return new_game

    def join_game(self, code):
        """Joins an existing game with the given code"""
        game = Game.query.filter_by(code=code).first()

        if game:
            gp_assoc = GamePlayerAssociation()
            gp_assoc.player_id = self.id
            gp_assoc.game_id = game.id
            db.session.add(gp_assoc)
            db.session.commit()
            return True
        return False
    
    def send_message(self, game_id, text):
        """Sends a message in the game chat"""
        message = Message()
        message.player_id = self.id
        message.game_id = game_id
        message.text = text

        db.session.add(message)
        db.session.commit()

    def send_friend_request(self, player_id):
        """Sends a friend request to the player with given id"""
        player = Player.query.get(player_id)
        if player:
            friend_request = FriendRequest()
            friend_request.sender_id = self.id
            friend_request.receiver_id = player_id
            db.session.add(friend_request)
            db.session.commit()
            return True
        return False
    
    def get_friend_requests(self):
        """Gets all friend requests sent to this player"""
        return FriendRequest.query.filter_by(receiver_id=self.id).all()
    
    def accept_friend_request(self, request_id):
        """Accepts a friend request"""
        request = FriendRequest.query.get(request_id)
        if request:
            friendship = Friendship()
            friendship.player1_id = request.sender_id
            friendship.player2_id = request.receiver_id
            
            db.session.add(friendship)
            db.session.commit()
            return True
        return False
    
    def get_all_friends(self):
        """Returns all friends of this player"""
        friends = Friendship.query.filter(Friendship.player1_id == self.id
                                          | Friendship.player2_id == self.id).all()
        return friends
    
    def make_move(self, game_id, tile_number):
        """Makes a move in a single game"""
        game = Game.query.get(game_id)
        if game:
            if Move.query.filter(Move.game_id == game_id
                                 & Move.tile_number == tile_number):
                return False
            move = Move()
            move.player_id = self.id
            move.game_id = game_id
            move.tile_number = tile_number
            db.session.add(move)
            db.session.commit(move)
            return True
        return False


class Game(db.Model, BaseModel):
    """Model for the tic-tac-toe game"""
    __tablename__ = "games"
    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(db.String(10), unique=True)
    difficulty = db.Column(db.Integer, default=0)
    finished = db.Column(db.Boolean, default=False)
    moves = db.relationship("Move", backref="moved_game", # For lack of a better term
                            cascade="all, delete, delete-orphan")
    messages = db.relationship("Message", backref="messaged_game")

    def __init__(self):
        self.code = self.generate_random_code(8)

    def generate_random_code(self, length):
        return "".join(random.SystemRandom().choice(string.ascii_uppercase + string.digits)
                       for _ in range(length))


class Move(db.Model, BaseModel):
    """Model for a single move in a game"""
    __tablename__ = "moves"
    id = db.Column(db.Integer, primary_key=True)
    tile_number = db.Column(db.Integer, nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"))
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)


class Message(db.Model, BaseModel):
    """Model for messages sent by players during games"""
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"))
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"))


class Friendship(db.Model):
    """Model for friendship amongst players"""
    __tablename__ = "friendships"
    id = db.Column(db.Integer, primary_key=True)
    player1_id = db.Column(db.Integer, db.ForeignKey("players.id"))
    player2_id = db.Column(db.Integer, db.ForeignKey("players.id"))


class FriendRequest(db.Model):
    """Model for friend requests"""
    __tablename__ = "friend_requests"
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("players.id"))
    receiver_id = db.Column(db.Integer, db.ForeignKey("players.id"))