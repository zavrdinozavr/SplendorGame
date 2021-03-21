import json
import random


class GemSet:
    """Creating class gem set"""
    def __init__(self, gem_list: list):
        keys = ["brown", "white", "red", "green", "blue"]
        self.gems = {key : gem for (key, gem) in zip(keys, gem_list)}

    def __gt__(self, other: 'GemSet'):
        for key in self.gems.keys():
            if self.gems[key] < other.gems[key]:
                return False
        return True

    def __add__(self, other: 'GemSet'):
        result = []
        for key in self.gems.keys():
            result.append(self.gems[key] + other.gems[key])
        return GemSet(result)

    def __sub__(self, other: 'GemSet'):
        result = []
        for key in self.gems.keys():
            result.append(max(0, self.gems[key] - other.gems[key]))
        return GemSet(result)

    def __str__(self):
        return ' '.join([str(gem) for gem in self.gems.values()])

    def get_gems_list(self):
        return list(self.gems.values())

    def get_keys(self) -> 'dict_keys':
        return self.gems.keys()

    def get_gems(self, gem_key: str) -> int:
        return self.gems[gem_key]

    def add_gems(self, gem_key: str, amount: int):
        self.gems[gem_key] += max(0, amount)

    def remove_gems(self, gem_key: str, amount: int):
        self.gems[gem_key] = max(0, self.gems[gem_key] - amount)

    def get_count(self) -> int:
        return sum(self.gems.values())


class Bank:
    """Contains gems and check rules for deal with it"""
    def __init__(self, players_number: int):
        gems_per_color = 7
        if players_number == 2:
            gems_per_color = 4
        elif players_number == 3:
            gems_per_color = 5
        gems = [gems_per_color for _ in range(5)]
        self.gems = GemSet(gems)

    def __str__(self):
        return str(self.gems)

    def get_gems_count(self):
        return self.gems.get_gems_list()

    def add_gemset(self, gemset: 'GemSet'):
        self.gems += gemset

    def can_take_three_different(self, colors: list) -> bool:
        if len(set(colors)) != 3:
            return False
        for color in colors:
            if not self.gems.get_gems(color):
                return False
        return True

    def take_three_different(self, colors: list):
        for color in colors:
            self.gems.remove_gems(color, 1)
        gems_list = []
        for key in self.gems.get_keys():
            if key in colors:
                gems_list.append(1)
            else:
                gems_list.append(0)
        return GemSet(gems_list)

    def can_take_two_same(self, color: str) -> bool:
        if self.gems.get_gems(color) >= 4:
            return True
        return False

    def take_two_same(self, color: str) -> bool:
        self.gems.remove_gems(color, 2)
        gemset = GemSet([0, 0, 0, 0, 0])
        gemset.add_gems(color, 2)
        return gemset


class Card:
    """Class Card"""
    def __init__(self, card_id: str, color: str, points: int, price: list):
        self.id_string = card_id
        self.color = color
        self.points = points
        self.price = GemSet(price)

    def can_be_bought(self, assets: 'GemSet', bonus: 'GemSet') -> bool:
        return (self.price - (assets + bonus)).get_count() == 0

    def __str__(self):
        return f"Id: {self.id_string}, Price: {self.price}"

    def __repr__(self):
        return f"Card({self.id_string}, {self.price})"


class Deck:
    """Contains objects of class Card"""
    def __init__(self, cards: dict):
        self.deck = [Card(card_id, **card_values)
                     for (card_id, card_values) in cards.items()]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.deck)

    def pop(self) -> 'Card':
        if self.deck:
            return self.deck.pop()
        return None


class CardField:
    """Contains objects of class Deck"""
    def __init__(self, decks: list):
        self.decks = [Deck(deck) for deck in decks]
        self.cards_in_row = 4 # The number of cards in a row of open cards
        self.open_cards = [[] for i in range(len(decks))]

    def __str__(self):
        res = ''
        for row in self.open_cards:
            res += repr(row) + '\n'
        return res

    def get_decks_card_count(self):
        return [len(d.deck) for d in self.decks]

    def get_opencards_ids(self):
        result = []
        for row in self.open_cards:
            row_cards = []
            for card in row:
                if card:
                    row_cards.append(card.id_string)
                    continue
                row_cards.append('')
            result.append(row_cards)
        return result

    def lay_out(self):
        for (deck, cards_row) in zip(self.decks, self.open_cards):
            for _ in range(self.cards_in_row):
                cards_row.append(deck.pop())

    def pop_card(self, pos: tuple) -> 'Card':
        (row, col) = pos
        if (row < len(self.open_cards)) and (col < self.cards_in_row):
            card = self.open_cards[row][col]
            self.open_cards[row][col] = self.decks[row].pop()
            return card
        print(f"Index Error: {pos}")
        return None

    def get_card(self, pos: tuple) -> 'Card':
        (row, col) = pos
        if (row < len(self.open_cards)) and (col < self.cards_in_row):
            return self.open_cards[row][col]
        print(f"Index Error: {pos}")
        return None


class Player:
    """Main and only game character"""
    def __init__(self, name: str):
        self.name = name
        self.assets = GemSet([0, 0, 0, 0, 0])
        self.bonus = GemSet([0, 0, 0, 0, 0])
        self.points = 0

    def add_gemset(self, gemset: 'GemSet'):
        self.assets += gemset

    def remove_gemset(self, gemset: 'GemSet'):
        self.assets -= gemset

    def get_token_count(self) -> int:
        return self.assets.get_count()

    def get_pay_info(self) -> list:
        return [self.assets, self.bonus]

    def add_card(self, card: 'Card') -> list:
        """Returns gems that must be returned to the bank"""
        gems_for_return = ((card.price - self.bonus)
                           - (card.price - self.bonus - self.assets))
        self.bonus.add_gems(card.color, 1)
        self.points += card.points
        self.remove_gemset(gems_for_return)
        return gems_for_return


class Game:
    """Main class of all this bullshit"""
    def __init__(self, players: list):
        self.players = [Player(player) for player in players]
        self.cur_p_ind = 0
        self.bank = Bank(len(players))
        self.game_over = False
        self.init_cardfield()

    def init_cardfield(self):
        with open('decks.json', 'r') as jdecks:
            decks = json.load(jdecks)
            self.cardfield = CardField(list(decks.values()))

    def lay_out_all(self):
        self.cardfield.lay_out()

    def take_three_gems(self, colors: list) -> bool:
        if self.bank.can_take_three_different(colors):
            self.players[self.cur_p_ind].add_gemset(self.bank.take_three_different(colors))
            return True
        print(f"Can't take 3 different gems: {colors}")
        return False

    def take_two_gems(self, color: str) -> bool:
        if self.bank.can_take_two_same(color):
            self.players[self.cur_p_ind].add_gemset(self.bank.take_two_same(color))
            return True
        print(f"Can't take 2 same gems: {color}")
        return False

    def buy_board_card(self, pos: tuple) -> bool:
        card = self.cardfield.get_card(pos)
        if card:
            if card.can_be_bought(*self.players[self.cur_p_ind].get_pay_info()):
                return_gems = self.players[self.cur_p_ind].add_card(card)
                self.cardfield.pop_card(pos)
                self.bank.add_gemset(return_gems)
                return True
            print(f"Can't afford that card: {pos}.")
        else:
            print(f"Card[{pos}] doesn't exist.")
        return False

    def encode_state(self):
        encode_state = json.dumps(
            {
                "winner": self.game_over * str(self.cur_p_ind),
                "current_player": str(self.cur_p_ind),
                "players": {
                    "0": {
                        "name": self.players[0].name,
                        "assets": self.players[0].assets.get_gems_list(),
                        "bonus": self.players[0].bonus.get_gems_list(),
                        "points": self.players[0].points
                    },
                    "1": {
                        "name": self.players[1].name,
                        "assets": self.players[1].assets.get_gems_list(),
                        "bonus": self.players[1].bonus.get_gems_list(),
                        "points": self.players[1].points
                    }
                },
                "cardfield": {
                    "open_cards": self.cardfield.get_opencards_ids(),
                    "decks_card_count": self.cardfield.get_decks_card_count(),
                },
                "bank": {
                    "gems": self.bank.get_gems_count()
                }
            }
        )
        return encode_state

    def end_turn_checks(self):
        if self.players[self.cur_p_ind].points >= 15:
            self.game_over = True
        self.cur_p_ind = (self.cur_p_ind + 1) % 2
