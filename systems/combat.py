"""
Combat system with projectiles, spells, and weapon mechanics
"""
import pygame
import random
from settings import FIRE, WATER, SAND, LAVA, STONE, AIR, TILE_SIZE


class Projectile:
    """Projectile cho combat system"""
    
    def __init__(self, x, y, vx, vy, material=FIRE, damage=10, lifetime=60):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.material = material
        self.damage = damage
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = 2
        self.visible = True
        
    def update(self, world):
        """Update projectile physics"""
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1  # Gravity
        self.lifetime -= 1
        
        if self.lifetime <= 0:
            self.visible = False
            return
            
        # Check collision with terrain
        mat = world.get_pixel(int(self.x), int(self.y))
        if mat != AIR:
            # Create impact effect
            self.explode(world)
            self.visible = False
            
    def explode(self, world):
        """Create explosion/impact effect"""
        radius = 3
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx*dx + dy*dy <= radius*radius:
                    x, y = int(self.x) + dx, int(self.y) + dy
                    if 0 <= x < world.width and 0 <= y < world.height:
                        # Place material
                        if random.random() < 0.7:
                            world.set_pixel(x, y, self.material)
                            
    def render(self, renderer):
        """Render projectile"""
        if not self.visible:
            return
        sx, sy = renderer.world_to_screen(int(self.x), int(self.y))
        color = (255, 100, 0) if self.material == FIRE else (64, 164, 223)
        pygame.draw.circle(renderer.screen, color, (sx, sy), self.size * renderer.tile_size)


class Wand:
    """Wand/spell casting system"""
    
    def __init__(self):
        self.spells = []
        self.current_spell = 0
        self.mana = 100
        self.max_mana = 100
        self.recharge_rate = 0.5
        
    def add_spell(self, spell):
        """Add spell to wand"""
        self.spells.append(spell)
        
    def cast(self, caster_x, caster_y, direction, world, renderer):
        """Cast current spell"""
        if not self.spells:
            return None
            
        spell = self.spells[self.current_spell]
        if self.mana < spell.mana_cost:
            return None
            
        self.mana -= spell.mana_cost
        
        # Create projectile
        projectile = spell.create_projectile(caster_x, caster_y, direction)
        
        # Camera shake for powerful spells
        if spell.shake_intensity > 0:
            renderer.add_shake(spell.shake_intensity, spell.shake_duration)
            
        return projectile
        
    def update(self):
        """Update mana recharge"""
        if self.mana < self.max_mana:
            self.mana = min(self.max_mana, self.mana + self.recharge_rate)
            
    def next_spell(self):
        """Cycle to next spell"""
        if self.spells:
            self.current_spell = (self.current_spell + 1) % len(self.spells)
            
    def prev_spell(self):
        """Cycle to previous spell"""
        if self.spells:
            self.current_spell = (self.current_spell - 1) % len(self.spells)


class Spell:
    """Spell definition"""
    
    def __init__(self, name, material, damage, speed, mana_cost, 
                 spread=0, count=1, shake_intensity=0, shake_duration=0):
        self.name = name
        self.material = material
        self.damage = damage
        self.speed = speed
        self.mana_cost = mana_cost
        self.spread = spread
        self.count = count
        self.shake_intensity = shake_intensity
        self.shake_duration = shake_duration
        
    def create_projectile(self, x, y, direction):
        """Create projectile(s) for this spell"""
        projectiles = []
        
        for i in range(self.count):
            # Calculate velocity with spread
            angle_spread = random.uniform(-self.spread, self.spread)
            vx = direction * self.speed * 0.8
            vy = self.speed * 0.6 + angle_spread
            
            proj = Projectile(x, y, vx, vy, self.material, self.damage)
            projectiles.append(proj)
            
        return projectiles if len(projectiles) > 1 else projectiles[0] if projectiles else None


# Pre-defined spells
SPELLS = {
    'spark': Spell('Spark', FIRE, 5, 8, 5, spread=0.1),
    'fireball': Spell('Fireball', FIRE, 15, 6, 15, spread=0.2, count=1, shake_intensity=3, shake_duration=5),
    'water_bolt': Spell('Water Bolt', WATER, 8, 7, 8, spread=0.15),
    'acid_stream': Spell('Acid Stream', 9, 3, 5, 10, spread=0.3, count=3),
    'explosion': Spell('Explosion', LAVA, 30, 4, 40, spread=0.5, shake_intensity=10, shake_duration=15),
}


class CombatSystem:
    """Main combat system manager"""
    
    def __init__(self):
        self.projectiles = []
        self.active_combat = False
        
    def spawn_projectile(self, projectile):
        """Add projectile to simulation"""
        self.projectiles.append(projectile)
        
    def update(self, world):
        """Update all projectiles"""
        i = 0
        while i < len(self.projectiles):
            proj = self.projectiles[i]
            proj.update(world)
            if not proj.visible:
                self.projectiles.pop(i)
            else:
                i += 1
                
    def render(self, renderer):
        """Render all projectiles"""
        for proj in self.projectiles:
            proj.render(renderer)
            
    def clear(self):
        """Clear all projectiles"""
        self.projectiles = []
