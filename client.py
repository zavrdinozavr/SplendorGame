import json
import pygame as pg
import socket
import sys, time

HEADER_LENGTH = 5
BACKGROUND = (140, 122, 230)
WHITE = (255, 255, 255)
GREY = (128, 128, 128)
GREEN = (0, 128, 0)
YELLOW = (180, 180, 0)
BLACK = (0, 0, 0)
COLORS = {
    "1": [(53, 59, 72), (47, 54, 64),],
    "2": [(245, 246, 250), (220, 221, 225)],
    "3": [(232, 65, 24), (194, 54, 22)],
    "4": [(76, 209, 55), (68, 189, 50)],
    "5": [(72, 126, 176), (64, 115, 158)]
}
REQUESTS = {
    "buy_card": "0",
    "take_two_gems": "1",
    "take_three_gems": "2",
    "finish_turn": "3",
}

def write_formated_digit(surface: 'pg.Surface', digit: str,
                          coords: tuple, color=WHITE):
    fonts = [[pg.font.Font(None, 111), BLACK],
             [pg.font.Font(None, 85), BLACK],
             [pg.font.Font(None, 100), color]]
    x, y = coords
    for font, i, j in zip(fonts, [x-2, x+3, x], [y-3, y+5, y]):
        surface.blit(font[0].render(str(digit), 1, font[1]), (i, j))


class GGemsInfo(pg.Surface):
    def __init__(self, assets: list, bonus: list):
        super(GGemsInfo, self).__init__((600, 100))
        self.info = []
        for i in range(5):
            gem = {"surf_1": pg.Surface((108, 90)),
                   "surf_2": pg.Surface((49, 80)),
                   "x_coord": 10 + 118 * i}
            self.info.append(gem)
        self.update(assets, bonus)

    def update(self, assets: list, bonus: list):
        self.fill(GREY)
        for gem, asset, bon, color in zip(self.info, assets, bonus, COLORS.values()):
            gem['surf_1'].fill(color[1])
            gem['surf_2'].fill(color[0])
            if bon:
                write_formated_digit(gem['surf_2'], str(bon), (6, 10))
            gem['surf_1'].blit(gem['surf_2'], (5, 5))
            if asset:
                write_formated_digit(gem['surf_1'], str(asset), (63, 15))
            self.blit(gem['surf_1'], (gem["x_coord"], 5))


class GCard(pg.Surface):
    def __init__(self, id: str):
        super(GCard, self).__init__((130, 180))
        self.update(id)

    def update(self, id: str):
        if not id:
            self.fill(GREY)
            return
        color = COLORS[id[0]][1]
        price_list = list(filter(lambda x: x[0] != '0', zip(id[2:], COLORS.values())))
        points = id[1]
        self.fill(color)
        write_formated_digit(self, points, (80, 0))
        i = 0
        for price in price_list:
            x, y = (23 + 41*(i % 3), 90 + 60*(i // 3))
            pg.draw.circle(self, price[1][0], (x, y), 18)
            p_1 = pg.font.Font(None, 47).render(price[0], 1, BLACK)
            p_2 = pg.font.Font(None, 57).render(price[0], 1, BLACK)
            p_3 = pg.font.Font(None, 50).render(price[0], 1, WHITE)
            self.blit(p_1, (x - 9, y - 14))
            self.blit(p_2, (x - 10, y - 17))
            self.blit(p_3, (x - 9, y - 15))
            i += 1


class GCardField(pg.Surface):
    def __init__(self, size: tuple, open_cards: list, decks_card_count: list):
        super(GCardField, self).__init__((size))
        self.open_cards = [[GCard(id) for id in row] for row in open_cards]
        self.decks = [pg.Surface((130, 180))] * 3
        self.update(open_cards, decks_card_count)

    def update(self, update_cards: list, decks_card_count: list):
        self.fill(BACKGROUND)
        j = 0
        for (row_1, row_2) in zip(self.open_cards, update_cards):
            i = 0
            for (card, card_id) in zip(row_1, row_2):
                card.update(card_id)
                self.blit(card, (135 * i, 185 * j))
                i += 1
            j += 1
        i = 0
        decks_colors = [(51, 161, 34), (186, 189, 25), (27, 122, 181)]
        for (deck, count, col) in zip(self.decks, decks_card_count, decks_colors):
            deck.fill(col)
            g_count = pg.font.Font(None, 100).render(str(count), 1, WHITE)
            deck.blit(g_count, (25, 50))
            self.blit(deck, (570, 185 * i))
            i += 1


class GPlayer(pg.Surface):
    def __init__(self, name: str, assets: list, bonus: list):
        super(GPlayer, self).__init__((850, 100))
        self.name = pg.font.Font(None, 36).render(name, 1, WHITE)
        self.info = GGemsInfo(assets, bonus)

    def update(self, assets: list, bonus: list, points: int):
        self.fill(GREY)
        score = pg.font.Font(None, 40).render(f'Score: {points}', 1, WHITE)
        self.info.update(assets, bonus)
        self.blit(self.name, (10, 10))
        self.blit(score, (10, 50))
        self.blit(self.info, (220, 0))


class GBank(pg.Surface):
    def __init__(self, size: tuple, gems: list):
        super(GBank, self).__init__(size)
        self.gems = []
        for i in range(5):
            gem = {"surf": pg.Surface((size[0], size[0])),
                   "y_coord": size[0] * i}
            self.gems.append(gem)
        self.update(gems)

    def update(self, gems: list):
        self.fill(BACKGROUND)
        rad = round(self.get_width() / 2)
        for gem, count, color in zip(self.gems, gems, COLORS.values()):
            gem['surf'].fill(BACKGROUND)
            pg.draw.circle(gem['surf'], color[0], (rad, rad), rad)
            write_formated_digit(gem['surf'], count, (16, 4))
            self.blit(gem['surf'], (0, gem['y_coord']))


class GButton(pg.Surface):
    def __init__(self, name: str, coords: tuple, size: tuple, button_id: int, font_size: int):
        super(GButton, self).__init__(size)
        self.font_size = font_size
        self.coords = coords
        self.size = size
        self.button_id = button_id
        self.name = pg.font.Font(None, self.font_size).render(name, 1, WHITE)

    def update(self, condition: int):
        if condition == 0:
            self.fill(GREY)
        elif condition == 1:
            self.fill(YELLOW)
        else:
            self.fill(GREEN)
        self.blit(self.name, (30, 25))

    def check_click(self, pos):
        if self.coords[0] < pos[0] < self.coords[0] + self.size[0]:
            if self.coords[1] < pos[1] < self.coords[1] + self.size[1]:
                return self.button_id
        return False


class State:
    def __init__(self, player_id: str, state: str):
        self.id = [player_id, str((int(player_id) + 1) % 2)]    # [player_id, opponent_id]
        self.block = False
        self.update(state)

    def update(self, upd_state: str):
        state = json.loads(upd_state)
        self.winner = state['winner']
        self.cur_player = state['current_player']
        self.players = state['players']
        self.cardfield = state['cardfield']
        self.bank = state['bank']


class GGame:
    def __init__(self, player_id: str, player_socket, init_state: str):
        pg.init()
        pg.display.set_caption("Splendor Game")
        pg.time.delay(100)
        self.size = (890, 800)
        self.cardfield_coords = [(20, 120), (700, 550)]
        self.bank_coords = [(770, 160), (70, 350)]
        self.screen = pg.display.set_mode(self.size)
        self.done = False
        self.p_socket = player_socket
        self.state_init(player_id, init_state)

    def state_init(self, player_id: str, init_state: str):
        self.state = State(player_id, init_state)
        self.players_init()
        self.field_init()
        self.buttons_init()

    def players_init(self):
        player = self.state.players[self.state.id[0]]
        oppon = self.state.players[self.state.id[1]]
        self.player = GPlayer(player['name'], player['assets'], player['bonus'])
        self.opponent = GPlayer(oppon['name'], oppon['assets'], oppon['bonus'])

    def field_init(self):
        self.cardfield = GCardField(self.cardfield_coords[1],
                                    self.state.cardfield['open_cards'],
                                    self.state.cardfield['decks_card_count'])
        self.bank = GBank(self.bank_coords[1], self.state.bank['gems'])

    def buttons_init(self):
        self.buttons = {}
        self.buttons['complete_move'] = GButton("OK", (755, 550), (100, 70), 1, 36)

    def update(self):
        player = self.state.players[self.state.id[0]]
        oppon = self.state.players[self.state.id[1]]
        if self.state.winner:
            self.done = True
        self.player.update(player['assets'], player['bonus'], player['points'])
        self.opponent.update(oppon['assets'], oppon['bonus'], oppon['points'])
        self.cardfield.update(self.state.cardfield['open_cards'],
                              self.state.cardfield['decks_card_count'])
        self.bank.update(self.state.bank['gems'])
        btn_cond = int(self.state.id[0] == self.state.cur_player) + int(self.state.block)
        self.buttons['complete_move'].update(btn_cond)

    def draw(self):
        self.update()
        self.screen.fill(BACKGROUND)
        self.screen.blit(self.player, (20, 700))
        self.screen.blit(self.opponent, (20, 0))
        self.screen.blit(self.cardfield, self.cardfield_coords[0])
        self.screen.blit(self.bank, self.bank_coords[0])
        for button in self.buttons.values():
            self.screen.blit(button, button.coords)
        pg.display.update()

    def check_button_click(self, pos):
        for button in self.buttons.values():
            clicked_button = button.check_click(pos)
            if clicked_button:
                return clicked_button
        return False

    def check_card_click(self, pos):
        (x, y), (w, h) = self.cardfield_coords
        if pos[0] < x or pos[0] > (x + w - 165) or pos[1] < y or pos[1] > (y + h):
            return False
        click_pos = (pos[0] - x, pos[1] - y)
        card_coord = (click_pos[1] // 185, click_pos[0] // 135)
        return card_coord

    def check_bank_click(self, pos):
        (x, y), (w, h) = self.bank_coords
        if pos[0] < x or pos[0] > (x + w) or pos[1] < y or pos[1] > (y + h):
            return False
        num = (pos[1] - y) // w
        rad = round(w / 2)
        x_r, y_r = ((pos[0] - rad - x), ((pos[1] - y) % w - rad))
        if (x_r ** 2 + y_r ** 2) < rad ** 2:
            return num
        return False

    def get_response(self):
        while True:
            try:
                reply = recieve_message(self.p_socket)
                break
            except IOError:
                continue
        if reply != 'False':
            self.state.update(reply)
            return True
        return False

    def request_buy_card(self, pos):
        send_message(self.p_socket, '{}{}{}'.format(REQUESTS['buy_card'], *pos))
        return self.get_response()

    def request_take_three_gems(self, gems: list):
        send_message(self.p_socket, '{}{}{}{}'.format(REQUESTS['take_three_gems'], *gems))
        return self.get_response()

    def request_take_two_gems(self, gem_id: int):
        send_message(self.p_socket, '{}{}'.format(REQUESTS['take_two_gems'], gem_id))
        return self.get_response()

    def request_finish_turn(self):
        send_message(self.p_socket, REQUESTS['finish_turn'])
        return self.get_response()

    def gameover(self):
        is_win = self.state.winner == self.state.id[1]
        result = is_win * 'You won!' + (not is_win) * 'You lose!'
        res_surf = pg.font.Font(None, 150).render(result, 1, (200, 50, 50))
        self.screen.fill(BACKGROUND)
        self.screen.blit(res_surf, (210, 340))
        pg.display.update()
        time.sleep(3)

    def mouse_event_handler(self, event, clicked_gems: list):
        if self.state.cur_player != self.state.id[0] or event.button != 1:
            return
        card = self.check_card_click(event.pos)
        gem = self.check_bank_click(event.pos)
        button = self.check_button_click(event.pos)
        if not gem is False:
            clicked_gems.append(gem)
            if len(clicked_gems) == 3 and len(set(clicked_gems)) == 3:
                if self.request_take_three_gems(clicked_gems):
                    self.state.block = True
                clicked_gems.clear()
            if len(clicked_gems) == 2 and len(set(clicked_gems)) == 1:
                if self.request_take_two_gems(gem):
                    self.state.block = True
                clicked_gems.clear()
            if len(clicked_gems) >= 3:
                clicked_gems.clear()
        if card:
            if self.request_buy_card(card):
                self.state.block = True
            clicked_gems.clear()
        if button == 1:
            self.state.block = False
            self.request_finish_turn()
            clicked_gems.clear()

    def main(self):
        clicked_gems = []
        while not self.done:
            if self.state.cur_player != self.state.id[0]:
                try:
                    resp = recieve_message(self.p_socket)
                    if resp != 'False':
                        self.state.update(resp)
                except IOError:
                    pass
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.done = True
                if event.type == pg.MOUSEBUTTONDOWN:
                    self.mouse_event_handler(event, clicked_gems)
            self.draw()
        self.gameover()


def send_message(client_socket, message: str):
    message = message.encode('utf-8')
    message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket.send(message_header + message)

def recieve_message(client_socket):
    message_header = client_socket.recv(HEADER_LENGTH)
    if not message_header:
        print('Connection lost!')
        client_socket.close()
        sys.exit()
        return False
    message_length = int(message_header.decode('utf-8').strip())
    message = client_socket.recv(message_length).decode('utf-8')
    return message


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Please enter IP and port')
        sys.exit()

    IP = str(sys.argv[1])
    PORT = int(sys.argv[2])

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    client_socket.setblocking(False)

    while True:
        username = input("Username: ").encode('utf-8')
        if len(username) < 16:
            break
        print("Username is too long! Try less than 16 symbols, please.")
    client_socket.send(username)

    while True:
        try:
            mes = recieve_message(client_socket)
            if not mes:
                print('Connection closed by server')
                sys.exit()
            break
        except IOError:
            continue
    print('Game started')
    GGame(mes[0], client_socket, mes[1:]).main()
    client_socket.close()
