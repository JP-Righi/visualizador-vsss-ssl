import pygame
import sys
import math
from enum import Enum

# Configurações do Pygame
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
INFO_PANEL_WIDTH = 300
FIELD_PANEL_WIDTH = WINDOW_WIDTH - INFO_PANEL_WIDTH

# Cores
GREEN = (0, 128, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
ORANGE = (255, 165, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)


class GameMode(Enum):
    SSL = 1
    VSSS = 2


# Parâmetros das modalidades em milímetros
MODALITY_PARAMS = {
    GameMode.SSL: {
        "field_size": (4500, 3000),
        "robot_radius": 90,  # 180mm de diâmetro
        "robot_shape": "circle",
        "ball_radius": 21.5,  # 43mm de diâmetro
        "goalkeeper_area_size": (500, 1350),
        "center_circle_size": 1000,
        "goal_size": (800, 200, 200)  # (largura, profundidade, altura)
    },
    GameMode.VSSS: {
        "field_size": (1500, 1200),
        "robot_radius": 40,  # 80mm de lado (metade para o centro)
        "robot_shape": "square",
        "ball_radius": 21.5,  # mesmo tamanho que SSL
        "goalkeeper_area_size": (150, 700),
        "center_circle_size": 400,
        "goal_size": (400, 100, 100)  # (largura, profundidade, altura)
    }
}


class Robot:
    def __init__(self, robot_id, x, y, orientation, team):
        self.id = robot_id
        self.x = x  # mm
        self.y = y  # mm
        self.orientation = orientation  # radianos (0 no eixo X)
        self.team = team  # 'blue' ou 'yellow'


class Ball:
    def __init__(self, x, y):
        self.x = x  # mm
        self.y = y  # mm


class SoccerVisualizer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(
            "Robotic Soccer Visualizer - ROS2 Integration Ready")
        self.font = pygame.font.SysFont('Arial', 16)
        self.big_font = pygame.font.SysFont('Arial', 24)

        # Dados iniciais
        self.game_mode = GameMode.SSL
        self.robots = []
        self.ball = Ball(0, 0)
        self.scale_factor = 1.0
        self.field_offset_x = 50
        self.field_offset_y = 50

        # Adiciona alguns robôs de exemplo
        self.add_sample_robots()

    def add_sample_robots(self):
        """Adiciona robôs de exemplo para demonstração"""
        params = MODALITY_PARAMS[self.game_mode]
        field_w, field_h = params["field_size"]

        # Robôs azuis
        for i in range(3):
            self.robots.append(Robot(
                i,
                field_w * 0.25,
                field_h * (0.25 + i*0.25),
                0, 'blue'
            ))

        # Robôs amarelos
        for i in range(3):
            self.robots.append(Robot(
                i+3,
                field_w * 0.75,
                field_h * (0.25 + i*0.25),
                math.pi, 'yellow'
            ))

        # Bola no centro
        self.ball = Ball(field_w / 2, field_h / 2)

    def update_robots(self, robot_data):
        """Atualiza os robôs com dados recebidos da visão"""
        self.robots = []
        for data in robot_data:
            self.robots.append(Robot(
                data.id,
                data.x_mm,  # Posição X em mm
                data.y_mm,  # Posição Y em mm
                data.orientation_rad,  # Orientação em radianos
                data.team  # 'blue' ou 'yellow'
            ))

    def update_game_mode(self, new_mode):
        """Altera a modalidade do jogo"""
        self.game_mode = new_mode
        self.robots = []
        self.add_sample_robots()
        self.calculate_scale_factor()

    def calculate_scale_factor(self):
        """Calcula o fator de escala para desenhar o campo na tela"""
        params = MODALITY_PARAMS[self.game_mode]
        field_w, field_h = params["field_size"]

        # Calcula o maior fator de escala que cabe no painel do campo
        scale_w = (FIELD_PANEL_WIDTH - 2*self.field_offset_x) / field_w
        scale_h = (WINDOW_HEIGHT - 2*self.field_offset_y) / field_h
        self.scale_factor = min(scale_w, scale_h)

    def mm_to_px(self, mm_x, mm_y):
        """Converte coordenadas em mm para pixels na tela"""
        px_x = self.field_offset_x + mm_x * self.scale_factor
        px_y = self.field_offset_y + mm_y * self.scale_factor
        return px_x, px_y

    def draw_field(self):
        """Desenha o campo com goleiras dinâmicas"""
        params = MODALITY_PARAMS[self.game_mode]
        field_w, field_h = params["field_size"]
        goal_w, goal_d, _ = params["goal_size"]  # Ignoramos a altura pois é 2D

        # Conversão para pixels
        field_px_w = field_w * self.scale_factor
        field_px_h = field_h * self.scale_factor
        field_px_x, field_px_y = self.mm_to_px(0, 0)
        goal_px_w = goal_w * self.scale_factor
        goal_px_d = goal_d * self.scale_factor

        # Campo principal
        pygame.draw.rect(self.screen, GREEN,
                         (field_px_x, field_px_y, field_px_w, field_px_h))

        # Linhas brancas
        pygame.draw.rect(self.screen, WHITE,
                         (field_px_x, field_px_y, field_px_w, field_px_h), 2)

        # Linha central
        center_x = field_px_x + field_px_w / 2
        pygame.draw.line(self.screen, WHITE,
                         (center_x, field_px_y),
                         (center_x, field_px_y + field_px_h), 2)

        # Círculo central
        center_circle_diameter = params["center_circle_size"]
        center_circle_radius_px = (
            center_circle_diameter / 2) * self.scale_factor
        pygame.draw.circle(self.screen, WHITE,
                           (center_x, field_px_y + field_px_h / 2),
                           center_circle_radius_px, 1)

        # Áreas do goleiro
        goal_area_w, goal_area_h = params["goalkeeper_area_size"]
        goal_area_px_w = goal_area_w * self.scale_factor
        goal_area_px_h = goal_area_h * self.scale_factor

        pygame.draw.rect(self.screen, WHITE,
                         (field_px_x, field_px_y + field_px_h/2 - goal_area_px_h/2,
                          goal_area_px_w, goal_area_px_h), 1)
        pygame.draw.rect(self.screen, WHITE,
                         (field_px_x + field_px_w - goal_area_px_w,
                          field_px_y + field_px_h/2 - goal_area_px_h/2,
                          goal_area_px_w, goal_area_px_h), 1)

        # Elementos específicos do VSSS
        if self.game_mode == GameMode.VSSS:
            # Conversão para pixels
            field_px_x, field_px_y = self.mm_to_px(0, 0)
            field_px_w = field_w * self.scale_factor
            field_px_h = field_h * self.scale_factor

            # Marcas em '+' (cruzamentos)
            cross_size = 20 * self.scale_factor  # Tamanho das cruzes
            cross_positions = [
                (field_w/4, field_h/2),       # Centro esquerdo
                (3*field_w/4, field_h/2),     # Centro direito
                (field_w/4, field_h/5.2),       # Centro superior esquerdo
                (3*field_w/4, field_h/5.2),     # Centro superior direito
                # Centro inferior esquerdo
                (field_w/4, field_h - field_h/5.2),
                (3*field_w/4, field_h - field_h/5.2),   # Centro inferior direito
            ]

            for pos_x, pos_y in cross_positions:
                px_x, px_y = self.mm_to_px(pos_x, pos_y)
                # Linha horizontal
                pygame.draw.line(self.screen, WHITE,
                                 (px_x - cross_size, px_y),
                                 (px_x + cross_size, px_y), 2)
                # Linha vertical
                pygame.draw.line(self.screen, WHITE,
                                 (px_x, px_y - cross_size),
                                 (px_x, px_y + cross_size), 2)

            # Cantos chanfrados (diagonais)
            corner_size = 70 * self.scale_factor  # Tamanho do chanfro
            corners = [
                # (canto_x, canto_y, direção_x, direção_y)
                (0, 70, 1, -1),           # Superior esquerdo
                (field_w - 5, 70, -1, -1),     # Superior direito
                (0, field_h - 75, 1, 1),     # Inferior esquerdo
                (field_w-5, field_h-75, -1, 1)  # Inferior direito
            ]

            for corner_x, corner_y, dir_x, dir_y in corners:
                start_x, start_y = self.mm_to_px(corner_x, corner_y)
                end_x = start_x + corner_size * dir_x
                end_y = start_y + corner_size * dir_y
                pygame.draw.line(self.screen, WHITE,
                                 (start_x, start_y),
                                 (end_x, end_y), 2)

        # Goleiras dinâmicas
        for side in ['left', 'right']:
            # Determina a cor da borda baseada nos robôs mais próximos
            border_color = WHITE  # Default
            min_dist = float('inf')

            for robot in self.robots:
                # Calcula distância ao centro da goleira
                goal_center_x = 0 if side == 'left' else field_w
                dist = math.sqrt((robot.x - goal_center_x) **
                                 2 + (robot.y - field_h/2)**2)

                if dist < min_dist:
                    min_dist = dist
                    border_color = BLUE if robot.team == 'blue' else YELLOW

            # Pontos da goleira
            if side == 'left':
                goal_points = [
                    (field_px_x, field_px_y + field_px_h/2 - goal_px_w/2),
                    (field_px_x - goal_px_d, field_px_y +
                     field_px_h/2 - goal_px_w/2),
                    (field_px_x - goal_px_d, field_px_y +
                     field_px_h/2 + goal_px_w/2),
                    (field_px_x, field_px_y + field_px_h/2 + goal_px_w/2)
                ]
            else:
                goal_points = [
                    (field_px_x + field_px_w, field_px_y +
                     field_px_h/2 - goal_px_w/2),
                    (field_px_x + field_px_w + goal_px_d,
                     field_px_y + field_px_h/2 - goal_px_w/2),
                    (field_px_x + field_px_w + goal_px_d,
                     field_px_y + field_px_h/2 + goal_px_w/2),
                    (field_px_x + field_px_w, field_px_y + field_px_h/2 + goal_px_w/2)
                ]

            # Desenha goleira (verde com borda colorida)
            pygame.draw.polygon(self.screen, GREEN, goal_points)
            pygame.draw.polygon(self.screen, border_color, goal_points, 2)

    def draw_robot(self, robot):
        """Desenha um robô de acordo com a modalidade atual"""
        params = MODALITY_PARAMS[self.game_mode]
        robot_px_x, robot_px_y = self.mm_to_px(robot.x, robot.y)
        robot_px_radius = int(params["robot_radius"] * self.scale_factor)

        color = BLUE if robot.team == 'blue' else YELLOW

        if params["robot_shape"] == "circle":
            # Versão simplificada e funcional para SSL
            # 1. Criamos uma lista de pontos para o círculo truncado
            points = []
            start_angle = -150  # Começa a 160° no sentido anti-horário
            end_angle = 150     # Termina a 160° no sentido horário

            # Adiciona pontos do arco
            for angle in range(start_angle, end_angle + 1, 5):
                rad = math.radians(angle)
                x = robot_px_x + robot_px_radius * \
                    math.cos(rad + robot.orientation + math.pi)
                y = robot_px_y + robot_px_radius * \
                    math.sin(rad + robot.orientation + math.pi)
                points.append((x, y))

            # Adiciona os pontos do segmento reto
            rad_start = math.radians(start_angle) + robot.orientation + math.pi
            rad_end = math.radians(end_angle) + robot.orientation + math.pi
            points.append((
                robot_px_x + robot_px_radius * math.cos(rad_end),
                robot_px_y + robot_px_radius * math.sin(rad_end)
            ))
            points.append((
                robot_px_x + robot_px_radius * math.cos(rad_start),
                robot_px_y + robot_px_radius * math.sin(rad_start)
            ))

            # Desenha o polígono
            pygame.draw.polygon(self.screen, color, points)

            # Linha de orientação
            end_x = robot_px_x + robot_px_radius * \
                0.8 * math.cos(robot.orientation)
            end_y = robot_px_y + robot_px_radius * \
                0.8 * math.sin(robot.orientation)
            pygame.draw.line(self.screen, BLACK,
                             (robot_px_x, robot_px_y),
                             (end_x, end_y), 2)
        else:
            # Robô quadrado (VSSS) - versão corrigida
            # Cria uma superfície para o robô com a frente para a direita (0 rad)
            robot_surface = pygame.Surface((robot_px_radius*2, robot_px_radius*2),
                                           pygame.SRCALPHA)

            # Desenha o quadrado (centrado)
            pygame.draw.rect(robot_surface, color,
                             (0, 0, robot_px_radius*2, robot_px_radius*2))

            # Desenha a linha de orientação (para a direita inicialmente)
            front_center = (robot_px_radius*2, robot_px_radius)
            back_center = (0, robot_px_radius)
            pygame.draw.line(robot_surface, BLACK,
                             (robot_px_radius, robot_px_radius),
                             front_center, 2)

            # Rotaciona o robô inteiro (incluindo a linha) pelo ângulo de orientação
            rotated = pygame.transform.rotate(
                robot_surface, -math.degrees(robot.orientation))
            rot_rect = rotated.get_rect(center=(robot_px_x, robot_px_y))
            self.screen.blit(rotated, rot_rect)

        # ID do robô (agora desenhamos por último para ficar sempre visível)
        text = self.font.render(str(robot.id), True, BLACK)
        text_rect = text.get_rect(center=(robot_px_x, robot_px_y))
        self.screen.blit(text, text_rect)

    def draw_ball(self):
        """Desenha a bola"""
        params = MODALITY_PARAMS[self.game_mode]
        ball_px_x, ball_px_y = self.mm_to_px(self.ball.x, self.ball.y)
        ball_px_radius = params["ball_radius"] * self.scale_factor

        pygame.draw.circle(self.screen, ORANGE,
                           (ball_px_x, ball_px_y),
                           ball_px_radius)

    def draw_info_panel(self):
        """Desenha o painel de informações à direita"""
        # Fundo do painel
        pygame.draw.rect(self.screen, GRAY,
                         (FIELD_PANEL_WIDTH, 0, INFO_PANEL_WIDTH, WINDOW_HEIGHT))

        # Título
        title = self.big_font.render("Informações do Jogo", True, BLACK)
        self.screen.blit(title, (FIELD_PANEL_WIDTH + 20, 20))

        # Modalidade atual
        mode_text = self.font.render(
            f"Modalidade: {'SSL' if self.game_mode == GameMode.SSL else 'VSSS'}",
            True, BLACK)
        self.screen.blit(mode_text, (FIELD_PANEL_WIDTH + 20, 60))

        # Dimensões do campo
        params = MODALITY_PARAMS[self.game_mode]
        field_w, field_h = params["field_size"]
        dim_text = self.font.render(
            f"Campo: {field_w}x{field_h} mm", True, BLACK)
        self.screen.blit(dim_text, (FIELD_PANEL_WIDTH + 20, 90))

        # Info dos robôs
        robot_title = self.font.render("Robôs:", True, BLACK)
        self.screen.blit(robot_title, (FIELD_PANEL_WIDTH + 20, 130))

        for i, robot in enumerate(self.robots):
            robot_info = self.font.render(
                f"ID {robot.id}: ({robot.x:.0f}, {robot.y:.0f}) mm, "
                f"{math.degrees(robot.orientation):.1f}°",
                True, BLUE if robot.team == 'blue' else YELLOW)
            self.screen.blit(robot_info, (FIELD_PANEL_WIDTH + 20, 160 + i*30))

        # Info da bola
        ball_title = self.font.render("Bola:", True, BLACK)
        self.screen.blit(ball_title, (FIELD_PANEL_WIDTH +
                         20, 160 + len(self.robots)*30))

        ball_info = self.font.render(
            f"Posição: ({self.ball.x:.0f}, {self.ball.y:.0f}) mm",
            True, ORANGE)
        self.screen.blit(ball_info, (FIELD_PANEL_WIDTH +
                         20, 190 + len(self.robots)*30))

    def run(self):
        """Loop principal do visualizador"""
        self.calculate_scale_factor()
        clock = pygame.time.Clock()

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.update_game_mode(GameMode.SSL)
                    elif event.key == pygame.K_2:
                        self.update_game_mode(GameMode.VSSS)

            # Atualizações (aqui você integraria com ROS2)
            # Exemplo: mover robôs para demonstração
            for robot in self.robots:
                robot.orientation += 0.02
                if robot.orientation > 2*math.pi:
                    robot.orientation -= 2*math.pi

            # Desenha tudo
            self.screen.fill(BLACK)
            self.draw_field()

            for robot in self.robots:
                self.draw_robot(robot)

            self.draw_ball()
            self.draw_info_panel()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    visualizer = SoccerVisualizer()
    visualizer.run()
