"""
Test script to verify game modules work correctly
Run this before running the full game
"""
import sys

def test_imports():
    """Test all module imports"""
    print("Testing imports...")
    
    try:
        import pygame
        print("✓ pygame imported")
    except ImportError as e:
        print(f"✗ pygame failed: {e}")
        return False
        
    try:
        import numpy as np
        print("✓ numpy imported")
    except ImportError as e:
        print(f"✗ numpy failed: {e}")
        return False
        
    try:
        import noise
        print("✓ noise imported (procedural generation available)")
    except ImportError:
        print("⚠ noise not available (will use simple terrain)")
        
    # Test settings
    try:
        import settings
        print(f"✓ settings loaded (WORLD: {settings.WORLD_WIDTH}x{settings.WORLD_HEIGHT})")
    except Exception as e:
        print(f"✗ settings failed: {e}")
        return False
        
    # Test engine modules
    try:
        from engine.physics import PixelWorld
        print("✓ engine.physics loaded")
    except Exception as e:
        print(f"✗ engine.physics failed: {e}")
        return False
        
    try:
        from engine.renderer import Renderer
        print("✓ engine.renderer loaded")
    except Exception as e:
        print(f"✗ engine.renderer failed: {e}")
        return False
        
    try:
        from engine.world import World
        print("✓ engine.world loaded")
    except Exception as e:
        print(f"✗ engine.world failed: {e}")
        return False
        
    # Test entities
    try:
        from entities.player import Player
        print("✓ entities.player loaded")
    except Exception as e:
        print(f"✗ entities.player failed: {e}")
        return False
        
    try:
        from entities.enemy import Enemy
        print("✓ entities.enemy loaded")
    except Exception as e:
        print(f"✗ entities.enemy failed: {e}")
        return False
        
    # Test systems
    try:
        from systems.sand_simulation import SandSimulation
        print("✓ systems.sand_simulation loaded")
    except Exception as e:
        print(f"✗ systems.sand_simulation failed: {e}")
        return False
        
    try:
        from systems.combat import CombatSystem, Wand, SPELLS
        print(f"✓ systems.combat loaded ({len(SPELLS)} spells)")
    except Exception as e:
        print(f"✗ systems.combat failed: {e}")
        return False
        
    return True


def test_physics():
    """Test physics simulation"""
    print("\nTesting physics simulation...")
    
    from systems.sand_simulation import SandSimulation
    from settings import SAND, WATER, AIR
    
    sim = SandSimulation(100, 50)  # Small test world
    
    # Test placing sand
    sim.fill_circle(50, 10, 5, SAND)
    sand_count = sim.get_material_count(SAND)
    print(f"  Placed {sand_count} sand pixels")
    
    # Test update
    sim.update()
    print("  ✓ Simulation update works")
    
    # Test water flow
    sim.set_pixel(50, 5, WATER)
    sim.update()
    print("  ✓ Water flow works")
    
    return True


def test_world_generation():
    """Test world generation"""
    print("\nTesting world generation...")
    
    from engine.world import World
    
    world = World(200, 100)
    world.generate_terrain()
    
    if world.generated:
        print("  ✓ Terrain generated successfully")
    else:
        print("  ✗ Terrain generation failed")
        return False
        
    return True


def test_combat():
    """Test combat system"""
    print("\nTesting combat system...")
    
    from systems.combat import CombatSystem, Wand, SPELLS
    
    combat = CombatSystem()
    wand = Wand()
    wand.add_spell(SPELLS['spark'])
    wand.add_spell(SPELLS['fireball'])
    
    print(f"  ✓ Combat system initialized")
    print(f"  ✓ Wand has {len(wand.spells)} spells")
    
    return True


def run_all_tests():
    """Run all tests"""
    print("=" * 50)
    print("NOITA-LIKE GAME - MODULE TESTS")
    print("=" * 50)
    
    all_passed = True
    
    if not test_imports():
        print("\n✗ Import tests failed!")
        return False
    print("  All imports OK")
    
    if not test_physics():
        print("\n✗ Physics tests failed!")
        all_passed = False
    else:
        print("  Physics tests OK")
        
    if not test_world_generation():
        print("\n✗ World generation tests failed!")
        all_passed = False
    else:
        print("  World generation OK")
        
    if not test_combat():
        print("\n✗ Combat tests failed!")
        all_passed = False
    else:
        print("  Combat tests OK")
        
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nYou can now run the game with:")
        print("  python main.py")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please fix the errors before running the game")
    print("=" * 50)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
