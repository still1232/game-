"""
Enemy entity with simple AI and pathfinding
"""
import pygame
import random
from settings import TILE_SIZE, FIRE, SAND


class Enemy:
    """Simple enemy với AI cơ bản"""
    
    def __init__(self, x, y, enemy_type='slime'):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        self.width = 3
        self.height = 3
        self.color = (200, 50, 50) if enemy_type == 'slime' else (100, 200, 50)
        
        # Stats
        self.hp = 30 if enemy_type == 'slime' else 20
        self.max_hp = self.hp
        self.damage = 10
        self.speed = 2
        
        # Physics
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        
        # AI state
        self.state = 'wander'  # wander, chase, attack
        self.target_x = None
        self.target_y = None
        self.wander_timer = 0
        self.attack_cooldown = 0
        
        # Visibility
        self.visible = True
        self.facing_right = True
        
        # Animation
        self.anim_frame = 0
        self.anim_timer = 0
        
        # Sprite frames (loaded from sprite sheet)
        self.sprites = []
        self.load_sprites()
        
    def load_sprites(self):
        """Load enemy sprites from external sprite sheet (Noita-like style)"""
        import os
        # Load different sprite sheets based on enemy type
        if self.enemy_type == 'slime':
            asset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'enemy_slime.png')
        elif self.enemy_type == 'fly':
            asset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'enemy_fly.png')
        else:
            asset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'enemy_sprite.png')
        
        try:
            sprite_sheet = pygame.image.load(asset_path).convert_alpha()
            # Extract frames from sprite sheet (assuming 16x16 pixel frames)
            frame_width = 16
            frame_height = 16
            cols = sprite_sheet.get_width() // frame_width
            
            # Get multiple animation frames
            for i in range(min(8, cols)):  # Load up to 8 frames
                frame = sprite_sheet.subsurface(i * frame_width, 0, frame_width, frame_height)
                # Scale to enemy size
                frame = pygame.transform.scale(frame, (self.width * TILE_SIZE, self.height * TILE_SIZE))
                self.sprites.append(frame)
        except Exception as e:
            print(f"Warning: Could not load enemy sprite sheet: {e}")
            # Create fallback sprite
            self._create_fallback_sprite()
            
    def _create_fallback_sprite(self):
        """Create simple fallback sprite if external file fails"""
        sprite = pygame.Surface((self.width * TILE_SIZE, self.height * TILE_SIZE), pygame.SRCALPHA)
        if self.enemy_type == 'slime':
            # Slime - green blob
            pygame.draw.ellipse(sprite, (50, 200, 50), 
                               (0, TILE_SIZE, self.width * TILE_SIZE, self.height * TILE_SIZE - TILE_SIZE))
            pygame.draw.circle(sprite, (255, 255, 255), 
                              (int(self.width * TILE_SIZE * 0.4), int(self.height * TILE_SIZE * 0.5)), 3)
            pygame.draw.circle(sprite, (255, 255, 255), 
                              (int(self.width * TILE_SIZE * 0.7), int(self.height * TILE_SIZE * 0.5)), 3)
        else:
            # Flying enemy
            pygame.draw.rect(sprite, (150, 50, 150),
                            (TILE_SIZE // 2, TILE_SIZE // 2, 
                             self.width * TILE_SIZE - TILE_SIZE, self.height * TILE_SIZE - TILE_SIZE))
        self.sprites.append(sprite)
            
    def get_sprite(self):
        """Get current sprite with animation support"""
        if not self.sprites:
            return None
            
        # Get current animation frame
        current_sprite = self.sprites[self.anim_frame % len(self.sprites)]
        
        if not self.facing_right:
            # Flip sprite if facing left
            return pygame.transform.flip(current_sprite, True, False)
        return current_sprite
        
    def get_rect(self):
        """Get collision rectangle"""
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        
    def update_ai(self, player, world):
        """Update AI behavior"""
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            
        # Calculate distance to player
        dx = player.x - self.x
        dy = player.y - self.y
        distance = (dx*dx + dy*dy) ** 0.5
        
        # State machine
        if self.state == 'wander':
            self.wander_timer -= 1
            if self.wander_timer <= 0:
                # Pick new wander direction
                self.target_x = self.x + random.randint(-50, 50)
                self.target_y = self.y + random.randint(-20, 20)
                self.wander_timer = random.randint(60, 180)
                
            # Move toward target
            if self.target_x is not None:
                if self.x < self.target_x:
                    self.vx = self.speed * 0.5
                    self.facing_right = True
                elif self.x > self.target_x:
                    self.vx = -self.speed * 0.5
                    self.facing_right = False
                    
            # Check if player is nearby
            if distance < 100:
                self.state = 'chase'
                
        elif self.state == 'chase':
            # Chase player
            if dx > 10:
                self.vx = self.speed
                self.facing_right = True
            elif dx < -10:
                self.vx = -self.speed
                self.facing_right = False
            else:
                self.vx = 0
                
            # Attack if close enough
            if distance < 30 and self.attack_cooldown <= 0:
                self.state = 'attack'
                self.attack_cooldown = 60
                
        elif self.state == 'attack':
            self.vx = 0
            # Deal damage to player
            if distance < 40:
                player.take_damage(self.damage)
            self.state = 'chase'
            
        # Apply gravity
        self.vy += 0.5
        
        # Update position
        self.x += self.vx
        self.y += self.vy
        
        # Collision
        self.check_collision(world)
        
        # Bounds
        self.x = max(0, min(self.x, world.width - self.width))
        self.y = max(0, min(self.y, world.height - self.height))
        
        # Animation
        self.anim_timer += 1
        if self.anim_timer >= 15:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 2
            
    def check_collision(self, world):
        """Simple collision with world"""
        # Vertical collision
        check_y = int(self.y + self.height) if self.vy > 0 else int(self.y)
        for x_off in range(self.width):
            mat = world.get_pixel(int(self.x + x_off), check_y)
            if mat != 0:
                if self.vy > 0:
                    self.y = check_y - self.height
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = check_y + 1
                    self.vy = 0
                break
                
        # Horizontal collision
        if self.vx != 0:
            front_x = int(self.x + self.width) if self.vx > 0 else int(self.x)
            for y_off in range(self.height):
                mat = world.get_pixel(front_x, int(self.y + y_off))
                if mat != 0:
                    if self.vx > 0:
                        self.x = front_x - self.width
                    else:
                        self.x = front_x + 1
                    self.vx = 0
                    break
                    
    def take_damage(self, amount):
        """Take damage"""
        self.hp -= amount
        if self.hp <= 0:
            self.die()
            
    def die(self):
        """Enemy death"""
        self.visible = False
        # Could spawn particles or drops here
        
    def render(self, renderer):
        """Render enemy"""
        if not self.visible:
            return
        renderer.render_entity(self)
