import pygame
import sys
import math
from enum import Enum
import random

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
# Agora usando coordenadas centradas no meio do campo
MODALITY_PARAMS = {
    GameMode.SSL: {
        "field_size": (4500, 3000),  # Total do campo
        "field_bounds": {"x_min": -2250, "x_max": 2250, "y_min": -1500, "y_max": 1500},
        "robot_radius": 90,  # 180mm de diâmetro
        "robot_shape": "circle",
        "ball_radius": 21.5,  # 43mm de diâmetro
        "goalkeeper_area_size": (500, 1350),
        "center_circle_size": 1000,
        "goal_size": (800, 200, 200)  # (largura, profundidade, altura)
    },
    GameMode.VSSS: {
        "field_size": (1500, 1200),  # Total do campo
        "field_bounds": {"x_min": -750, "x_max": 750, "y_min": -600, "y_max": 600},
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
        self.x = x  # mm (coordenadas centradas no meio do campo)
        self.y = y  # mm (coordenadas centradas no meio do campo)
        self.orientation = orientation  # radianos (0 no eixo X)
        self.team = team  # 'blue' ou 'yellow'


class Ball:
    def __init__(self, x, y):
        self.x = x  # mm (coordenadas centradas no meio do campo)
        self.y = y  # mm (coordenadas centradas no meio do campo)


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
        self.ball = Ball(0, 0)  # Bola no centro do campo (0,0)
        self.scale_factor = 1.0
        self.field_offset_x = 50
        self.field_offset_y = 50
        self.robot_paths = {}  # Exemplo: {robot_id: [Pose2D, Pose2D, ...]}

        # Adiciona alguns robôs de exemplo
        self.add_sample_robots()
        self.generate_paths_for_all_robots()

    def generate_random_path(self, start_x, start_y, num_points=5, step=300):
        path = []
        x, y = start_x, start_y
        path.append(type('Pose2D', (), {'x': x, 'y': y, 'theta': 0})())
        
        bounds = MODALITY_PARAMS[self.game_mode]["field_bounds"]
        
        for _ in range(num_points):
            x += random.randint(-step, step)
            y += random.randint(-step, step)
            
            # Mantém dentro dos limites do campo
            x = max(bounds["x_min"], min(bounds["x_max"], x))
            y = max(bounds["y_min"], min(bounds["y_max"], y))
            
            path.append(type('Pose2D', (), {'x': x, 'y': y, 'theta': 0})())
        return path

    def generate_paths_for_all_robots(self):
        for robot in self.robots:
            self.robot_paths[robot.id] = self.generate_random_path(robot.x, robot.y)

    def add_sample_robots(self):
        """Adiciona robôs de exemplo para demonstração usando coordenadas centradas"""
        bounds = MODALITY_PARAMS[self.game_mode]["field_bounds"]

        # Robôs azuis (lado esquerdo)
        for i in range(3):
            self.robots.append(Robot(
                i,
                bounds["x_min"] + abs(bounds["x_min"]) * 0.3,  # 30% da distância do lado esquerdo
                bounds["y_min"] + (bounds["y_max"] - bounds["y_min"]) * (0.25 + i*0.25),
                0, 'blue'
            ))

        # Robôs amarelos (lado direito)
        for i in range(3):
            self.robots.append(Robot(
                i+3,
                bounds["x_max"] - abs(bounds["x_max"]) * 0.3,  # 30% da distância do lado direito
                bounds["y_min"] + (bounds["y_max"] - bounds["y_min"]) * (0.25 + i*0.25),
                math.pi, 'yellow'
            ))

        # Bola no centro (0,0)
        self.ball = Ball(0, 0)

    def update_robots(self, robot_data):
        """Atualiza os robôs com dados recebidos da visão"""
        self.robots = []
        for data in robot_data:
            self.robots.append(Robot(
                data.id,
                data.x_mm,  # Posição X em mm (já centrada)
                data.y_mm,  # Posição Y em mm (já centrada)
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
        """Converte coordenadas em mm (centradas) para pixels na tela"""
        params = MODALITY_PARAMS[self.game_mode]
        field_w, field_h = params["field_size"]
        
        # Converte de coordenadas centradas para coordenadas com origem no canto
        field_coord_x = mm_x + field_w/2
        field_coord_y = mm_y + field_h/2
        
        # Converte para pixels
        px_x = self.field_offset_x + field_coord_x * self.scale_factor
        px_y = self.field_offset_y + field_coord_y * self.scale_factor
        return px_x, px_y

    def draw_field(self):
        """Desenha o campo com goleiras dinâmicas usando coordenadas centradas"""
        params = MODALITY_PARAMS[self.game_mode]
        bounds = params["field_bounds"]
        field_w, field_h = params["field_size"]
        goal_w, goal_d, _ = params["goal_size"]

        # Conversão para pixels
        field_px_w = field_w * self.scale_factor
        field_px_h = field_h * self.scale_factor
        field_px_x, field_px_y = self.mm_to_px(bounds["x_min"], bounds["y_min"])
        goal_px_w = goal_w * self.scale_factor
        goal_px_d = goal_d * self.scale_factor

        # Campo principal
        pygame.draw.rect(self.screen, GREEN,
                         (field_px_x, field_px_y, field_px_w, field_px_h))

        # Linhas brancas
        pygame.draw.rect(self.screen, WHITE,
                         (field_px_x, field_px_y, field_px_w, field_px_h), 2)

        # Linha central (x=0)
        center_x, _ = self.mm_to_px(0, 0)
        pygame.draw.line(self.screen, WHITE,
                         (center_x, field_px_y),
                         (center_x, field_px_y + field_px_h), 2)

        # Círculo central (centro em 0,0)
        center_circle_diameter = params["center_circle_size"]
        center_circle_radius_px = (center_circle_diameter / 2) * self.scale_factor
        center_px_x, center_px_y = self.mm_to_px(0, 0)
        pygame.draw.circle(self.screen, WHITE,
                           (center_px_x, center_px_y),
                           center_circle_radius_px, 1)

        # Áreas do goleiro
        goal_area_w, goal_area_h = params["goalkeeper_area_size"]
        goal_area_px_w = goal_area_w * self.scale_factor
        goal_area_px_h = goal_area_h * self.scale_factor

        # Área do goleiro esquerda
        left_goal_area_x, left_goal_area_y = self.mm_to_px(bounds["x_min"], -goal_area_h/2)
        pygame.draw.rect(self.screen, WHITE,
                         (left_goal_area_x, left_goal_area_y,
                          goal_area_px_w, goal_area_px_h), 1)

        # Área do goleiro direita
        right_goal_area_x, right_goal_area_y = self.mm_to_px(bounds["x_max"] - goal_area_w, -goal_area_h/2)
        pygame.draw.rect(self.screen, WHITE,
                         (right_goal_area_x, right_goal_area_y,
                          goal_area_px_w, goal_area_px_h), 1)

        # Elementos específicos do VSSS
        if self.game_mode == GameMode.VSSS:
            # Marcas em '+' (cruzamentos)
            cross_size = 20 * self.scale_factor
            cross_positions = [
                (-bounds["x_max"]/2, 0),           # Centro esquerdo
                (bounds["x_max"]/2, 0),            # Centro direito
                (-bounds["x_max"]/2, bounds["y_max"]/2.6),     # Centro superior esquerdo
                (bounds["x_max"]/2, bounds["y_max"]/2.6),      # Centro superior direito
                (-bounds["x_max"]/2, -bounds["y_max"]/2.6),    # Centro inferior esquerdo
                (bounds["x_max"]/2, -bounds["y_max"]/2.6),     # Centro inferior direito
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
            corner_size = 70 * self.scale_factor
            corner_offset = 70  # Distância do canto em mm
            
            corners = [
                (bounds["x_min"] + corner_offset, bounds["y_max"] - corner_offset, 1, -1),     # Superior esquerdo
                (bounds["x_max"] - corner_offset, bounds["y_max"] - corner_offset, -1, -1),    # Superior direito
                (bounds["x_min"] + corner_offset, bounds["y_min"] + corner_offset, 1, 1),      # Inferior esquerdo
                (bounds["x_max"] - corner_offset, bounds["y_min"] + corner_offset, -1, 1)      # Inferior direito
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
            border_color = WHITE
            min_dist = float('inf')

            for robot in self.robots:
                # Calcula distância ao centro da goleira
                goal_center_x = bounds["x_min"] if side == 'left' else bounds["x_max"]
                dist = math.sqrt((robot.x - goal_center_x)**2 + (robot.y - 0)**2)

                if dist < min_dist:
                    min_dist = dist
                    border_color = BLUE if robot.team == 'blue' else YELLOW

            # Pontos da goleira
            if side == 'left':
                goal_left_x, goal_top_y = self.mm_to_px(bounds["x_min"], -goal_w/2)
                goal_left_ext_x, _ = self.mm_to_px(bounds["x_min"] - goal_d, -goal_w/2)
                _, goal_bottom_y = self.mm_to_px(bounds["x_min"], goal_w/2)
                
                goal_points = [
                    (goal_left_x, goal_top_y),
                    (goal_left_ext_x, goal_top_y),
                    (goal_left_ext_x, goal_bottom_y),
                    (goal_left_x, goal_bottom_y)
                ]
            else:
                goal_right_x, goal_top_y = self.mm_to_px(bounds["x_max"], -goal_w/2)
                goal_right_ext_x, _ = self.mm_to_px(bounds["x_max"] + goal_d, -goal_w/2)
                _, goal_bottom_y = self.mm_to_px(bounds["x_max"], goal_w/2)
                
                goal_points = [
                    (goal_right_x, goal_top_y),
                    (goal_right_ext_x, goal_top_y),
                    (goal_right_ext_x, goal_bottom_y),
                    (goal_right_x, goal_bottom_y)
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
            points = []
            start_angle = -150
            end_angle = 150

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
            # Robô quadrado (VSSS)
            robot_surface = pygame.Surface((robot_px_radius*2, robot_px_radius*2),
                                           pygame.SRCALPHA)

            # Desenha o quadrado (centrado)
            pygame.draw.rect(robot_surface, color,
                             (0, 0, robot_px_radius*2, robot_px_radius*2))

            # Desenha a linha de orientação
            front_center = (robot_px_radius*2, robot_px_radius)
            pygame.draw.line(robot_surface, BLACK,
                             (robot_px_radius, robot_px_radius),
                             front_center, 2)

            # Rotaciona o robô
            rotated = pygame.transform.rotate(
                robot_surface, -math.degrees(robot.orientation))
            rot_rect = rotated.get_rect(center=(robot_px_x, robot_px_y))
            self.screen.blit(rotated, rot_rect)

        # ID do robô
        text = self.font.render(str(robot.id), True, BLACK)
        text_rect = text.get_rect(center=(robot_px_x, robot_px_y))
        self.screen.blit(text, text_rect)

    def draw_robot_path(self, robot_id):
        path = self.robot_paths.get(robot_id, [])
        if len(path) < 2:
            return

        # Converte os pontos do caminho para pixels
        points_px = [self.mm_to_px(pose.x, pose.y) for pose in path]

        # Desenha a polyline
        pygame.draw.lines(self.screen, ORANGE, False, points_px, 2)

        # Desenha pequenos círculos nos pontos
        for pt in points_px:
            pygame.draw.circle(self.screen, ORANGE, pt, 5)

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
        bounds = params["field_bounds"]
        dim_text = self.font.render(
            f"Campo: X({bounds['x_min']},{bounds['x_max']}) Y({bounds['y_min']},{bounds['y_max']})",
            True, BLACK)
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
                self.draw_robot_path(robot.id)
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
