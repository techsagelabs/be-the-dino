import cv2
import mediapipe as mp
import pygame
import random
import sys
import time
import numpy as np

# Initialize pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 500
GROUND_Y = 220
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Set up the game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Personalized Gesture-Controlled Dinosaur Game")
clock = pygame.time.Clock()

# MediaPipe hand detection setup
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)

# Start webcam
cap = cv2.VideoCapture(0)

# Function to detect jump gesture
def detect_jump_gesture(hand_landmarks):
    # Get wrist y position
    wrist_y = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].y

    # Check if hand is raised above threshold (approx. shoulder level)
    threshold = 0.5
    return wrist_y < threshold

# Function to capture player image and create dino
def capture_player_image():
    # Display countdown
    font = pygame.font.SysFont('Arial', 48)

    for i in range(3, 0, -1):
        # Read frame
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image")
            return None

        # Flip horizontally
        frame = cv2.flip(frame, 1)

        # Convert to pygame surface
        frame = cv2.resize(frame, (640, 480))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cam_surface = pygame.Surface((640, 480))
        pygame.surfarray.blit_array(cam_surface, frame_rgb.swapaxes(0, 1))

        # Clear screen
        screen.fill(WHITE)

        # Show camera feed
        screen.blit(cam_surface, (SCREEN_WIDTH//2 - 320, SCREEN_HEIGHT//2 - 240))

        # Draw countdown text
        countdown_text = font.render(f"Smile! Taking picture in {i}...", True, RED)
        screen.blit(countdown_text, (SCREEN_WIDTH//2 - countdown_text.get_width()//2, 30))

        # Show instructions
        instructions = font.render("Stand in frame to become the dinosaur!", True, BLACK)
        screen.blit(instructions, (SCREEN_WIDTH//2 - instructions.get_width()//2, SCREEN_HEIGHT - 50))

        pygame.display.flip()
        pygame.time.delay(1000)  # Wait 1 second between counts



    # Capture the final image
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture final image")
        return None

    frame = cv2.flip(frame, 1)

    # Flash effect
    screen.fill(WHITE)
    pygame.display.flip()
    pygame.time.delay(200)

    # Convert to pygame surface
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_surface = pygame.Surface((frame.shape[1], frame.shape[0]))
    pygame.surfarray.blit_array(frame_surface, frame_rgb.swapaxes(0, 1))

    # Extract player from image (simplified - just take center portion)
    player_width = min(frame.shape[1] // 3, 120)
    player_height = min(frame.shape[0] // 2, 140)
    center_x = frame.shape[1] // 2
    center_y = frame.shape[0] // 2

    player_img = frame_rgb[
        center_y - player_height//2:center_y + player_height//2, 
        center_x - player_width//2:center_x + player_width//2
    ]

    # Create pygame surface for player image
    player_surface = pygame.Surface((player_width, player_height))
    pygame.surfarray.blit_array(player_surface, player_img.swapaxes(0, 1))

    # Scale to dino size
    dino_width = 40
    dino_height = 60
    player_surface = pygame.transform.scale(player_surface, (dino_width, dino_height))

    # Display the captured image for a moment
    screen.fill(WHITE)
    screen.blit(player_surface, (SCREEN_WIDTH//2 - dino_width//2, SCREEN_HEIGHT//2 - dino_height//2))
    captured_text = font.render("This is your character!", True, BLACK)
    screen.blit(captured_text, (SCREEN_WIDTH//2 - captured_text.get_width()//2, 50))
    pygame.display.flip()
    pygame.time.delay(2000)  # Show for 2 seconds

    return player_surface

class Dino:
    def __init__(self, image=None):
        self.x = 50
        self.y = GROUND_Y
        self.width = 40
        self.height = 60
        self.is_jumping = False
        self.jump_velocity = 0
        self.gravity = 1
        self.image = image

    def draw(self):
        if self.image:
            # Draw the player's image
            screen.blit(self.image, (self.x, self.y - self.height))
        else:
            # Fallback to rectangle if no image
            pygame.draw.rect(screen, BLACK, (self.x, self.y - self.height, self.width, self.height))

    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.jump_velocity = -15  # Negative to go up

    def update(self):
        if self.is_jumping:
            self.y += self.jump_velocity
            self.jump_velocity += self.gravity

            # Check if landed
            if self.y >= GROUND_Y:
                self.y = GROUND_Y
                self.jump_velocity = 0
                self.is_jumping = False

class Obstacle:
    def __init__(self, x):
        self.x = x
        self.y = GROUND_Y
        self.width = 20
        self.height = 30 + random.randint(0, 30)
        self.passed = False
        # Random color for obstacles
        self.color = (random.randint(0, 200), random.randint(0, 200), random.randint(0, 200))

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y - self.height, self.width, self.height))

    def update(self, speed):
        self.x -= speed

    def check_collision(self, dino):
        # Add a small buffer to make collision detection more forgiving
        buffer = 5
        if (dino.x + buffer < self.x + self.width and
            dino.x + dino.width - buffer > self.x and
            dino.y - dino.height + buffer < self.y and
            dino.y - buffer > self.y - self.height):
            return True
        return False

def main():
    # Initial welcome screen
    font = pygame.font.SysFont('Arial', 32)
    small_font = pygame.font.SysFont('Arial', 24)

    screen.fill(WHITE)
    title = font.render("Personalized Dinosaur Game", True, BLACK)
    instr1 = small_font.render("1. We'll take your picture to create your character", True, BLACK)
    instr2 = small_font.render("2. Control your character by raising your hand to jump", True, BLACK)
    instr3 = small_font.render("3. Press SPACE to start", True, BLACK)

    screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
    screen.blit(instr1, (SCREEN_WIDTH//2 - instr1.get_width()//2, 120))
    screen.blit(instr2, (SCREEN_WIDTH//2 - instr2.get_width()//2, 160))
    screen.blit(instr3, (SCREEN_WIDTH//2 - instr3.get_width()//2, 200))

    pygame.display.flip()

    # Wait for space key to start
    waiting_for_start = True
    while waiting_for_start:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting_for_start = False

    # Capture player image for dinosaur
    player_image = capture_player_image()

    # Game variables
    dino = Dino(image=player_image)
    obstacles = []
    game_speed = 5
    obstacle_interval = 1500  # milliseconds
    score = 0
    game_over = False
    last_obstacle_time = pygame.time.get_ticks()

    # Camera display size
    cam_width = 320
    cam_height = 240

    # Font setup
    font = pygame.font.SysFont('Arial', 24)

    running = True
    while running:
        current_time = pygame.time.get_ticks()

        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over:
                    dino.jump()
                elif event.key == pygame.K_RETURN and game_over:
                    # Restart game
                    dino = Dino(image=player_image)
                    obstacles = []
                    game_speed = 5
                    score = 0
                    game_over = False

        # Process webcam frame
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image")
            break

        # Flip horizontally for a selfie-view display
        frame = cv2.flip(frame, 1)

        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame with MediaPipe
        results = hands.process(rgb_frame)

        # Draw hand landmarks on the image
        jump_detected = False
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Check for jump gesture
                jump_detected = detect_jump_gesture(hand_landmarks)

                # Make dino jump if gesture detected
                if jump_detected and not game_over:
                    dino.jump()

        # Add text to indicate if jump is detected
        status_text = "JUMP!" if jump_detected else "Ready"
        status_color = (0, 255, 0) if jump_detected else (0, 0, 255)  # Green or Red
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)

        # Convert frame to pygame surface for display
        frame = cv2.resize(frame, (cam_width, cam_height))
        cam_surface = pygame.Surface((cam_width, cam_height))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pygame.surfarray.blit_array(cam_surface, frame_rgb.swapaxes(0, 1))

        # Game logic (only if game is not over)
        if not game_over:
            # Update dinosaur
            dino.update()

            # Create new obstacles
            if current_time - last_obstacle_time > obstacle_interval:
                obstacles.append(Obstacle(SCREEN_WIDTH))
                last_obstacle_time = current_time
                # Make the game harder over time
                obstacle_interval = max(800, 1500 - score * 10)

            # Update obstacles
            for obstacle in obstacles[:]:
                obstacle.update(game_speed)

                # Check for collision
                if obstacle.check_collision(dino):
                    game_over = True

                # Add score when passing an obstacle
                if not obstacle.passed and obstacle.x + obstacle.width < dino.x:
                    obstacle.passed = True
                    score += 1
                    game_speed = min(15, 5 + score * 0.2)  # Cap speed at 15

                # Remove obstacles that are off-screen
                if obstacle.x + obstacle.width < 0:
                    obstacles.remove(obstacle)

        # Draw everything
        screen.fill(WHITE)

        # Draw clouds (simple decoration)
        for i in range(5):
            cloud_x = (current_time // 20 + i * 200) % (SCREEN_WIDTH + 200) - 100
            cloud_y = 50 + i * 15
            pygame.draw.ellipse(screen, GRAY, (cloud_x, cloud_y, 60, 30))
            pygame.draw.ellipse(screen, GRAY, (cloud_x + 20, cloud_y - 10, 60, 30))
            pygame.draw.ellipse(screen, GRAY, (cloud_x + 40, cloud_y, 60, 30))

        # Draw ground
        pygame.draw.line(screen, BLACK, (0, GROUND_Y), (SCREEN_WIDTH, GROUND_Y), 2)

        # Draw dinosaur and obstacles
        dino.draw()
        for obstacle in obstacles:
            obstacle.draw()

        # Draw score
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (10, 10))

        # Draw camera feed in the bottom right corner
        screen.blit(cam_surface, (SCREEN_WIDTH - cam_width - 10, SCREEN_HEIGHT - cam_height - 10))

        # Draw game over screen
        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)  # Semi-transparent
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            game_over_text = font.render("Game Over!", True, WHITE)
            score_display = font.render(f"Final Score: {score}", True, WHITE)
            restart_text = font.render("Press ENTER to restart", True, WHITE)

            screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 40))
            screen.blit(score_display, (SCREEN_WIDTH//2 - score_display.get_width()//2, SCREEN_HEIGHT//2))
            screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 40))

        pygame.display.flip()
        clock.tick(60)  # 60 FPS

    # Clean up
    cap.release()
    hands.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
