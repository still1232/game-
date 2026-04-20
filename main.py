"""
Main game entry point - Noita-like Pixel Physics Game
A 2D sandbox physics game with destructible terrain and elemental interactions
"""
import pygame
import sys
import numpy as np

# Import game modules
from settings import *
from engine.physics import PixelWorld
from engine.renderer import Renderer, Particle
from engine.world import World
from entities.player import Player
from entities.enemy import Enemy
from systems.combat import CombatSystem, Wand, SPELLS
from systems.sand_simulation import SandSimulation


class Game:
    """Main game class"""
    
    def __init__(self):
        # Initialize pygame
        pygame.init()
        pygame.mixer.init()
        
        # Create renderer
        self.renderer = Renderer(SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE)
        
        # Create world
        self.world = World(WORLD_WIDTH, WORLD_HEIGHT, CHUNK_SIZE)
        
        # Use sand simulation system (optimized)
        self.simulation = SandSimulation(WORLD_WIDTH, WORLD_HEIGHT)
        
        # Generate terrain
        self.world.generate_terrain()
        
        # Copy world grid to simulation
        self.simulation.grid = self.world.grid.copy()
        
        # Create player
        spawn_x = WORLD_WIDTH // 4
        spawn_y = 50
        self.player = Player(spawn_x, spawn_y)
        
        # Create wand with spells
        self.wand = Wand()
        self.wand.add_spell(SPELLS['spark'])
        self.wand.add_spell(SPELLS['fireball'])
        self.wand.add_spell(SPELLS['water_bolt'])
        
        # Combat system
        self.combat = CombatSystem()
        
        # Enemies
        self.enemies = []
        self.spawn_enemies(5)
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        
        # Game state
        self.running = True
        self.paused = False
        self.clock = pygame.time.Clock()
        self.fps_counter = 0
        self.frame_count = 0
        self.last_fps_update = 0
        
        # Mouse interaction
        self.mouse_held = False
        self.brush_size = 3
        self.brush_material = SAND
        
        print("=" * 50)
        print("NOITA-LIKE PIXEL PHYSICS GAME")
        print("=" * 50)
        print("\nControls:")
        print("  WASD/Arrows - Move")
        print("  Space - Jump")
        print("  Shift - Jetpack")
        print("  Mouse Click - Shoot/Place material")
        print("  1-5 - Change spell/material")
        print("  R - Respawn")
        print("  P - Pause")
        print("  ESC - Quit")
        print("=" * 50)
        
    def spawn_enemies(self, count):
        """Spawn enemies in the world"""
        for _ in range(count):
            ex = np.random.randint(100, WORLD_WIDTH - 100)
            ey = np.random.randint(50, WORLD_HEIGHT // 2)
            enemy_type = 'slime' if np.random.random() > 0.5 else 'flier'
            enemy = Enemy(ex, ey, enemy_type)
            self.enemies.append(enemy)
            
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                    print(f"Game {'paused' if self.paused else 'resumed'}")
                    
                elif event.key == pygame.K_r:
                    # Respawn player
                    self.player = Player(WORLD_WIDTH // 4, 50)
                    
                elif event.key == pygame.K_1:
                    self.wand.current_spell = 0
                    self.brush_material = FIRE
                    
                elif event.key == pygame.K_2:
                    self.wand.current_spell = 1
                    self.brush_material = WATER
                    
                elif event.key == pygame.K_3:
                    self.wand.current_spell = 2
                    self.brush_material = SAND
                    
                elif event.key == pygame.K_4:
                    self.brush_material = LAVA
                    
                elif event.key == pygame.K_5:
                    self.brush_material = STONE
                    
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_KP_PLUS:
                    self.brush_size = min(10, self.brush_size + 1)
                    
                elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                    self.brush_size = max(1, self.brush_size - 1)
                    
            elif event.type == pygame.KEYUP:
                pass
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_held = True
                if event.button == 1:  # Left click
                    self.use_tool()
                elif event.button == 3:  # Right click
                    self.clear_area()
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button in (1, 3):
                    self.mouse_held = False
                    
        # Continuous key states
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        
        # Mouse position for tools
        if self.mouse_held:
            self.use_tool()
            
    def use_tool(self):
        """Use selected tool at mouse position"""
        mx, my = pygame.mouse.get_pos()
        wx, wy = self.renderer.screen_to_world(mx, my)
        
        # Check if clicking on UI area
        if mx < 250 and my < 100:
            return
            
        # Place material
        for dy in range(-self.brush_size, self.brush_size + 1):
            for dx in range(-self.brush_size, self.brush_size + 1):
                if dx*dx + dy*dy <= self.brush_size*self.brush_size:
                    self.simulation.set_pixel(wx + dx, wy + dy, self.brush_material)
                    
    def clear_area(self):
        """Clear area at mouse position"""
        mx, my = pygame.mouse.get_pos()
        wx, wy = self.renderer.screen_to_world(mx, my)
        
        radius = self.brush_size
        self.simulation.explode(wx, wy, radius)
        self.renderer.add_shake(5, 8)
        
    def update(self):
        """Update game logic"""
        if self.paused:
            return
            
        # Update simulation (only near player for performance)
        self.simulation.update(
            self.player.x + self.player.width // 2,
            self.player.y + self.player.height // 2,
            update_radius=150
        )
        
        # Sync world grid with simulation
        self.world.grid = self.simulation.grid.copy()
        
        # Update player
        self.player.update(self.world)
        
        # Update camera to follow player
        target_cam_x = self.player.x * TILE_SIZE - SCREEN_WIDTH // 2
        target_cam_y = self.player.y * TILE_SIZE - SCREEN_HEIGHT // 2
        
        # Smooth camera movement
        self.camera_x += (target_cam_x - self.camera_x) * 0.1
        self.camera_y += (target_cam_y - self.camera_y) * 0.1
        
        self.renderer.set_camera(self.camera_x, self.camera_y)
        self.renderer.update_shake()
        
        # Update enemies
        for enemy in self.enemies:
            if enemy.visible:
                enemy.update_ai(self.player, self.world)
                
        # Update combat
        self.wand.update()
        self.combat.update(self.world)
        
        # Check projectile-enemy collisions
        for proj in self.combat.projectiles[:]:
            if proj.visible:
                for enemy in self.enemies[:]:
                    if enemy.visible:
                        dist = ((proj.x - enemy.x - enemy.width//2)**2 + 
                               (proj.y - enemy.y - enemy.height//2)**2) ** 0.5
                        if dist < enemy.width * TILE_SIZE:
                            enemy.take_damage(proj.damage)
                            proj.visible = False
                            break
                            
        # Remove dead enemies
        self.enemies = [e for e in self.enemies if e.visible]
        
        # Spawn new enemies occasionally
        if len(self.enemies) < 3 and np.random.random() < 0.01:
            self.spawn_enemies(1)
            
        # Update FPS counter
        self.frame_count += 1
        current_time = pygame.time.get_ticks()
        if current_time - self.last_fps_update >= 1000:
            self.fps_counter = self.frame_count
            self.frame_count = 0
            self.last_fps_update = current_time
            
    def render(self):
        """Render everything"""
        # Clear screen
        self.renderer.clear()
        
        # Render world
        self.renderer.render_world(self.world)
        
        # Render enemies
        for enemy in self.enemies:
            self.renderer.render_entity(enemy)
            
        # Render player
        self.renderer.render_entity(self.player)
        
        # Render projectiles
        self.combat.render(self.renderer)
        
        # Render particles
        self.renderer.render_particles()
        
        # Render UI
        self.player.render_ui(self.renderer.screen)
        
        # Render spell info
        font = pygame.font.Font(None, 24)
        spell_name = self.wand.spells[self.wand.current_spell].name if self.wand.spells else "None"
        text = font.render(f"Spell: {spell_name} | Mana: {int(self.wand.mana)}", True, (255, 255, 255))
        self.renderer.screen.blit(text, (20, 110))
        
        # Render brush info
        text = font.render(f"Brush: {self.brush_material} | Size: {self.brush_size}", True, (255, 255, 255))
        self.renderer.screen.blit(text, (20, 130))
        
        # Render FPS
        text = font.render(f"FPS: {self.fps_counter}", True, (255, 255, 0))
        self.renderer.screen.blit(text, (SCREEN_WIDTH - 100, 20))
        
        # Render pause message
        if self.paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.renderer.screen.blit(overlay, (0, 0))
            
            font_large = pygame.font.Font(None, 72)
            text = font_large.render("PAUSED", True, (255, 255, 255))
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.renderer.screen.blit(text, text_rect)
            
        # Update display
        pygame.display.flip()
        
    def shoot(self):
        """Player shooting"""
        direction = 1 if self.player.facing_right else -1
        projectile = self.wand.cast(
            self.player.x + self.player.width // 2,
            self.player.y + self.player.height // 2,
            direction,
            self.world,
            self.renderer
        )
        
        if projectile:
            if isinstance(projectile, list):
                for p in projectile:
                    self.combat.spawn_projectile(p)
            else:
                self.combat.spawn_projectile(projectile)
                
    def run(self):
        """Main game loop"""
        shoot_cooldown = 0
        
        while self.running:
            # Handle events
            self.handle_events()
            
            # Update
            self.update()
            
            # Shooting
            if shoot_cooldown > 0:
                shoot_cooldown -= 1
            else:
                keys = pygame.key.get_pressed()
                mouse_buttons = pygame.mouse.get_pressed()
                if mouse_buttons[0]:  # Left mouse button held
                    self.shoot()
                    shoot_cooldown = 10  # Auto-fire rate
                    
            # Render
            self.render()
            
            # Cap FPS
            self.clock.tick(FPS)
            
        # Cleanup
        pygame.quit()
        sys.exit()


def main():
    """Entry point"""
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)


if __name__ == "__main__":
    main()
