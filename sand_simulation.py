import pygame
import random
import sys

# 初始化 Pygame
pygame.init()

# 常量定义
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 1000
SAND_SIZE = 8  # Increased from 3 to 8 pixels
FPS = 60       # 调整帧率

# 颜色定义
BLACK = (0, 0, 0)
SAND_COLORS = [
    (255, 255, 0),  # Yellow
    (0, 0, 255),    # Blue
]

# 创建窗口
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Sand Simulation')
clock = pygame.time.Clock()

class SandGrain:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = random.choice(SAND_COLORS)
        self.settled = False
        self.sliding = False  # 是否正在滑动

class SandSimulation:
    def __init__(self):
        self.sand_particles = []
        self.grid = [[False for _ in range(WINDOW_HEIGHT // SAND_SIZE)] 
                    for _ in range(WINDOW_WIDTH // SAND_SIZE)]
        self.max_slope = 1
        self.slide_chance = 0.95
        self.height_threshold = 2
        self.square_size = 20
        self.connected_sand_timer = None
        self.sand_to_remove = None
        self.touch_delay = 20
        self.current_x = WINDOW_WIDTH // 2
        self.move_speed = 5 * SAND_SIZE
        self.active_square = None
        self.can_move = True  # Flag to control movement
        
    def is_square_landed(self):
        """Check if the current square has landed"""
        if not self.active_square:
            return True
            
        for sand in self.active_square:
            if not sand.settled:
                return False
        return True

    def move_left(self):
        if not self.can_move or not self.active_square:
            return
            
        # Check if any particle would go out of bounds
        leftmost = min(int(sand.x - self.move_speed) for sand in self.active_square 
                      if not sand.settled)
        if leftmost < 0:
            # Move only as far as the border
            offset = -min(int(sand.x) for sand in self.active_square 
                         if not sand.settled)
            if offset < 0:
                for sand in self.active_square:
                    if not sand.settled:
                        sand.x += offset
            return
            
        # Move all particles in active square
        for sand in self.active_square:
            if not sand.settled:
                new_x = sand.x - self.move_speed
                grid_x = int(new_x // SAND_SIZE)
                grid_y = int(sand.y // SAND_SIZE)
                if not self.grid[grid_x][grid_y]:
                    sand.x = new_x

    def move_right(self):
        if not self.can_move or not self.active_square:
            return
            
        # Check if any particle would go out of bounds
        rightmost = max(int(sand.x + self.move_speed) for sand in self.active_square 
                       if not sand.settled)
        if rightmost >= WINDOW_WIDTH:
            # Move only as far as the border
            offset = WINDOW_WIDTH - max(int(sand.x + SAND_SIZE) for sand in self.active_square 
                                      if not sand.settled)
            if offset > 0:
                for sand in self.active_square:
                    if not sand.settled:
                        sand.x += offset
            return
            
        # Move all particles in active square
        for sand in self.active_square:
            if not sand.settled:
                new_x = sand.x + self.move_speed
                grid_x = int(new_x // SAND_SIZE)
                grid_y = int(sand.y // SAND_SIZE)
                if not self.grid[grid_x][grid_y]:
                    sand.x = new_x
    
    def find_connected_sand(self, start_x, start_y, color, visited):
        """Find all connected sand particles of the same color using iterative flood fill"""
        if (start_x < 0 or start_x >= WINDOW_WIDTH//SAND_SIZE or
            start_y < 0 or start_y >= WINDOW_HEIGHT//SAND_SIZE or
            not self.grid[start_x][start_y] or
            (start_x, start_y) in visited):
            return set()
        
        # Get the sand particle at this position
        sand_at_pos = None
        for sand in self.sand_particles:
            if (int(sand.x//SAND_SIZE), int(sand.y//SAND_SIZE)) == (start_x, start_y):
                sand_at_pos = sand
                break
        
        # If no sand found or different color, return empty set
        if not sand_at_pos or sand_at_pos.color != color:
            return set()
        
        connected = set()
        stack = [(start_x, start_y)]
        
        while stack:
            x, y = stack.pop()
            
            if (x, y) in visited:
                continue
            
            # Check if current position has same-colored sand
            current_sand = None
            for sand in self.sand_particles:
                if (int(sand.x//SAND_SIZE), int(sand.y//SAND_SIZE)) == (x, y):
                    current_sand = sand
                    break
            
            if not current_sand or current_sand.color != color:
                continue
                
            visited.add((x, y))
            connected.add((x, y))
            
            # Check all 8 directions
            directions = [
                (0, 1), (0, -1), (1, 0), (-1, 0),
                (1, 1), (1, -1), (-1, 1), (-1, -1)
            ]
            for dx, dy in directions:
                next_x, next_y = x + dx, y + dy
                if (next_x >= 0 and next_x < WINDOW_WIDTH//SAND_SIZE and
                    next_y >= 0 and next_y < WINDOW_HEIGHT//SAND_SIZE and
                    self.grid[next_x][next_y] and
                    (next_x, next_y) not in visited):
                    stack.append((next_x, next_y))
        
        return connected
    
    def check_and_remove_connected_sand(self):
        """Check for same-colored sand that touches both bounds and remove it"""
        current_time = pygame.time.get_ticks()
        
        # Handle removal of previously identified connected sand
        if self.connected_sand_timer is not None:
            if current_time - self.connected_sand_timer >= 20:
                if self.sand_to_remove:
                    # Create a set of positions to remove for faster lookup
                    remove_positions = self.sand_to_remove
                    
                    # Update grid
                    for x, y in remove_positions:
                        self.grid[x][y] = False
                    
                    # Remove particles
                    self.sand_particles = [sand for sand in self.sand_particles 
                                         if (int(sand.x//SAND_SIZE), 
                                             int(sand.y//SAND_SIZE)) not in remove_positions]
                    
                    # Clear active square if all its particles were removed
                    if self.active_square:
                        self.active_square = [sand for sand in self.active_square 
                                            if sand in self.sand_particles]
                        
                self.connected_sand_timer = None
                self.sand_to_remove = None
            return

        # Start checking for connections
        visited = set()
        all_connected = set()
        
        # Check for connections from left wall
        for y in range(WINDOW_HEIGHT // SAND_SIZE):
            if not self.grid[0][y]:
                continue
                
            # Find sand at left wall
            left_sand = None
            for sand in self.sand_particles:
                if (int(sand.x//SAND_SIZE), int(sand.y//SAND_SIZE)) == (0, y):
                    left_sand = sand
                    break
            
            if left_sand:
                # Find all connected sand of the same color
                connected = self.find_connected_sand(0, y, left_sand.color, visited)
                
                # Check if this group reaches the right wall
                if any(x == (WINDOW_WIDTH//SAND_SIZE - 1) for x, _ in connected):
                    all_connected.update(connected)
        
        # If we found any valid connections, start the removal timer
        if all_connected:
            self.connected_sand_timer = current_time
            self.sand_to_remove = all_connected
    
    def add_sand_square(self, center_x):
        # Calculate the top-left corner of the square
        start_x = center_x - (self.square_size * SAND_SIZE) // 2
        
        # Choose one random color for the entire square
        square_color = random.choice(SAND_COLORS)
        
        # Store the new square's particles
        new_square = []
        
        # Add sand particles in a square pattern
        for row in range(self.square_size):
            for col in range(self.square_size):
                x = start_x + (col * SAND_SIZE)
                y = row * SAND_SIZE
                
                # Ensure the sand is within screen bounds
                if 0 <= x < WINDOW_WIDTH and 0 <= y < WINDOW_HEIGHT:
                    grid_x = int(x // SAND_SIZE)
                    grid_y = int(y // SAND_SIZE)
                    
                    if not self.grid[grid_x][grid_y]:
                        new_sand = SandGrain(x, y)
                        new_sand.color = square_color
                        new_square.append(new_sand)
                        self.sand_particles.append(new_sand)
        
        self.active_square = new_square
        self.can_move = True  # Reset movement control for new square
    
    def check_slope(self, x, y):
        # 检查左右两侧的高度差
        left_height = 0
        right_height = 0
        
        # 检查左侧高度差
        if x > 0:
            check_y = y
            while (check_y < (WINDOW_HEIGHT//SAND_SIZE) and 
                   not self.grid[x-1][check_y]):
                left_height += 1
                check_y += 1
                if left_height > self.height_threshold:
                    break
        
        # 检查右侧高度差
        if x < (WINDOW_WIDTH//SAND_SIZE)-1:
            check_y = y
            while (check_y < (WINDOW_HEIGHT//SAND_SIZE) and 
                   not self.grid[x+1][check_y]):
                right_height += 1
                check_y += 1
                if right_height > self.height_threshold:
                    break
        
        # 如果高度差超过阈值，决定滑落方向
        if left_height > self.height_threshold or right_height > self.height_threshold:
            # 优先向高度差更大的方向滑落
            if left_height > right_height:
                return -1 if x > 0 and not self.grid[x-1][y] else 0
            elif right_height > left_height:
                return 1 if x < (WINDOW_WIDTH//SAND_SIZE)-1 and not self.grid[x+1][y] else 0
            else:
                # 如果两边高度差相同，随机选择方向
                possible_dirs = []
                if x > 0 and not self.grid[x-1][y]:
                    possible_dirs.append(-1)
                if x < (WINDOW_WIDTH//SAND_SIZE)-1 and not self.grid[x+1][y]:
                    possible_dirs.append(1)
                return random.choice(possible_dirs) if possible_dirs else 0
        
        # 如果没有显著的高度差，检查普通的滑动条件
        left_empty = x > 0 and not self.grid[x-1][y]
        right_empty = x < (WINDOW_WIDTH//SAND_SIZE)-1 and not self.grid[x+1][y]
        
        if y < (WINDOW_HEIGHT//SAND_SIZE)-1:
            left_support = x > 0 and self.grid[x-1][y+1]
            center_support = self.grid[x][y+1]
            right_support = x < (WINDOW_WIDTH//SAND_SIZE)-1 and self.grid[x+1][y+1]
            
            if not center_support:
                if left_support and right_support:
                    return random.choice([-1, 1]) if random.random() < 0.5 else 0
                elif left_support and left_empty:
                    return 1
                elif right_support and right_empty:
                    return -1
                elif left_empty and right_empty:
                    return random.choice([-1, 1])
        return 0
    
    def update(self):
        any_movement = False
        
        # First check if active square has touched anything
        if self.active_square and self.can_move:
            for sand in self.active_square:
                if not sand.settled:
                    new_y = int((sand.y + SAND_SIZE) // SAND_SIZE)
                    new_x = int(sand.x // SAND_SIZE)
                    # Check if sand will hit ground or other sand
                    if (new_y >= WINDOW_HEIGHT//SAND_SIZE or 
                        (new_y < WINDOW_HEIGHT//SAND_SIZE and self.grid[new_x][new_y])):
                        self.can_move = False  # Disable movement once touched
                        break
        
        # Regular update for all particles
        for sand in self.sand_particles:
            initial_pos = (sand.x, sand.y)
            
            if sand.settled:
                x, y = int(sand.x // SAND_SIZE), int(sand.y // SAND_SIZE)
                slide_direction = self.check_slope(x, y)
                if slide_direction != 0 and random.random() < self.slide_chance:
                    self.grid[x][y] = False
                    sand.settled = False
                    new_x = (x + slide_direction) * SAND_SIZE
                    if 0 <= new_x < WINDOW_WIDTH and not self.grid[x + slide_direction][y]:
                        sand.x = new_x
                        any_movement = True
                continue
            
            new_x = int(sand.x // SAND_SIZE)
            new_y = int((sand.y + SAND_SIZE) // SAND_SIZE)
            
            if new_y >= WINDOW_HEIGHT//SAND_SIZE or self.grid[new_x][new_y]:
                current_y = int(sand.y // SAND_SIZE)
                slide_direction = self.check_slope(new_x, current_y)
                if slide_direction != 0:
                    test_x = new_x + slide_direction
                    if (0 <= test_x < WINDOW_WIDTH//SAND_SIZE and 
                        not self.grid[test_x][current_y]):
                        sand.x = test_x * SAND_SIZE
                        any_movement = True
                        continue
                
                sand.settled = True
                self.grid[new_x][current_y] = True
                sand.x = new_x * SAND_SIZE
                sand.y = current_y * SAND_SIZE
                continue
            
            if not self.grid[new_x][new_y]:
                sand.y += SAND_SIZE
                any_movement = True
            
            if (sand.x, sand.y) != initial_pos:
                any_movement = True
        
        # Check the connection of sand
        if not any_movement:
            self.check_and_remove_connected_sand()
    
    def draw(self, surface):
        for sand in self.sand_particles:
            pygame.draw.rect(surface, sand.color, 
                           (int(sand.x), int(sand.y), SAND_SIZE, SAND_SIZE))

def main():
    simulation = SandSimulation()
    running = True
    
    # Spawn the first square
    simulation.add_sand_square(WINDOW_WIDTH // 2)  # Reset current_x to center
    simulation.current_x = WINDOW_WIDTH // 2  # Reset spawn position

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Handle keyboard input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            simulation.move_left()
        if keys[pygame.K_RIGHT]:
            simulation.move_right()
        
        # Update sand positions
        simulation.update()
        
        # Spawn new square if previous one has landed
        if simulation.is_square_landed():
            simulation.current_x = WINDOW_WIDTH // 2  # Reset spawn position to center
            simulation.add_sand_square(simulation.current_x)
        
        # Draw
        screen.fill(BLACK)
        simulation.draw(screen)
        pygame.display.flip()
        
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()