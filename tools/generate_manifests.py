#!/usr/bin/env python3
"""
Generate manifest.json files for all tasks in a game.

Usage:
    python generate_manifests.py game01
    python generate_manifests.py game01 --task 01_default_namespace
    python generate_manifests.py game01 --overwrite
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional


# Phase mapping from test files to phase configuration
PHASE_MAPPING = {
    'test_01_setup.py': {
        'id': 'setup',
        'name': 'Setup',
        'description': 'Initialize the task environment',
        'points': 0,
        'required': True,
        'auto_run': False,
        'timeout_seconds': 30,
        'max_attempts': 3
    },
    'test_02_ready.py': {
        'id': 'ready',
        'name': 'Ready',
        'description': 'Verify prerequisites are met',
        'points': 5,
        'required': True,
        'auto_run': False,
        'timeout_seconds': 30,
        'max_attempts': 3
    },
    'test_03_answer.py': {
        'id': 'answer',
        'name': 'Answer',
        'description': 'Provide the solution',
        'points': 10,
        'required': True,
        'auto_run': False,
        'timeout_seconds': 30,
        'max_attempts': 3
    },
    'test_04_challenge.py': {
        'id': 'challenge',
        'name': 'Challenge',
        'description': 'Complete the main challenge',
        'points': 15,
        'required': True,
        'auto_run': False,
        'timeout_seconds': 60,
        'max_attempts': 5
    },
    'test_05_check.py': {
        'id': 'check',
        'name': 'Check',
        'description': 'Verify the solution is correct',
        'points': 20,
        'required': True,
        'auto_run': False,
        'timeout_seconds': 30,
        'max_attempts': 3
    },
    'test_06_cleanup.py': {
        'id': 'cleanup',
        'name': 'Cleanup',
        'description': 'Clean up task resources',
        'points': 0,
        'required': False,
        'auto_run': True,
        'timeout_seconds': 30,
        'max_attempts': 1
    }
}


def discover_phases(task_dir: Path) -> List[Dict]:
    """Discover phases by scanning for test files."""
    phases = []
    
    for test_file, config in PHASE_MAPPING.items():
        test_path = task_dir / test_file
        if test_path.exists():
            phase = config.copy()
            phase['test_file'] = test_file
            phases.append(phase)
    
    return phases


def extract_task_metadata(task_dir: Path, task_id: str) -> Dict:
    """Extract metadata from task directory."""
    # Generate title from task_id
    title = task_id.replace('_', ' ').title()
    
    # Try to extract description from instruction.md
    instruction_file = task_dir / 'instruction.md'
    description = f"Learn {title}"
    
    if instruction_file.exists():
        try:
            with open(instruction_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Use first non-empty line as description
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        description = line[:200]  # Limit to 200 chars
                        break
        except Exception:
            pass
    
    # Determine difficulty based on task number
    try:
        task_num = int(task_id.split('_')[0])
        if task_num <= 10:
            difficulty = 'beginner'
        elif task_num <= 20:
            difficulty = 'intermediate'
        else:
            difficulty = 'advanced'
    except (ValueError, IndexError):
        difficulty = 'beginner'
    
    return {
        'title': title,
        'description': description,
        'difficulty': difficulty
    }


def generate_manifest(task_dir: Path, task_id: str) -> Dict:
    """Generate a complete manifest for a task."""
    phases = discover_phases(task_dir)
    
    if not phases:
        raise ValueError(f"No test files found in {task_dir}")
    
    metadata = extract_task_metadata(task_dir, task_id)
    
    # Calculate estimated time based on phases
    estimated_minutes = len(phases) * 5  # 5 minutes per phase
    
    manifest = {
        'task_id': task_id,
        'title': metadata['title'],
        'description': metadata['description'],
        'difficulty': metadata['difficulty'],
        'estimated_minutes': estimated_minutes,
        'phases': phases,
        'prerequisites': [],
        'tags': ['kubernetes', 'kubectl'],
        'hints': [
            'Read the instruction carefully',
            'Use kubectl commands to complete the task',
            'Check the test results for detailed feedback'
        ]
    }
    
    return manifest


def save_manifest(manifest: Dict, task_dir: Path, overwrite: bool = False) -> bool:
    """Save manifest to task directory."""
    manifest_path = task_dir / 'manifest.json'
    
    if manifest_path.exists() and not overwrite:
        print(f"  ⚠️  Manifest already exists: {manifest_path}")
        print(f"     Use --overwrite to replace it")
        return False
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    return True


def process_task(game_dir: Path, task_id: str, overwrite: bool = False) -> bool:
    """Process a single task."""
    task_dir = game_dir / task_id
    
    if not task_dir.is_dir():
        print(f"  ❌ Task directory not found: {task_dir}")
        return False
    
    try:
        manifest = generate_manifest(task_dir, task_id)
        
        if save_manifest(manifest, task_dir, overwrite):
            phases_count = len(manifest['phases'])
            total_points = sum(p['points'] for p in manifest['phases'])
            print(f"  ✅ Generated manifest: {task_id}")
            print(f"     Phases: {phases_count}, Points: {total_points}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"  ❌ Error generating manifest for {task_id}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Generate manifest.json files for K8s game tasks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate manifests for all tasks in game01
  python generate_manifests.py game01
  
  # Generate manifest for specific task
  python generate_manifests.py game01 --task 01_default_namespace
  
  # Overwrite existing manifests
  python generate_manifests.py game01 --overwrite
  
  # Dry run (show what would be generated)
  python generate_manifests.py game01 --dry-run
        """
    )
    
    parser.add_argument('game', help='Game identifier (e.g., game01, game02)')
    parser.add_argument('--task', help='Specific task ID (optional)')
    parser.add_argument('--overwrite', action='store_true', 
                       help='Overwrite existing manifest.json files')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be generated without writing files')
    
    args = parser.parse_args()
    
    # Find game directory
    script_dir = Path(__file__).parent.parent
    tests_dir = script_dir / 'tests' / args.game
    
    if not tests_dir.is_dir():
        print(f"❌ Game directory not found: {tests_dir}")
        sys.exit(1)
    
    print(f"🎮 Processing game: {args.game}")
    print(f"📁 Directory: {tests_dir}")
    print()
    
    # Get list of tasks
    if args.task:
        tasks = [args.task]
    else:
        tasks = sorted([
            d.name for d in tests_dir.iterdir()
            if d.is_dir() and not d.name.startswith('_') and '99_test_template' not in d.name
        ])
    
    if not tasks:
        print("❌ No tasks found")
        sys.exit(1)
    
    print(f"📋 Found {len(tasks)} task(s)")
    print()
    
    # Process tasks
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for task_id in tasks:
        if args.dry_run:
            task_dir = tests_dir / task_id
            try:
                manifest = generate_manifest(task_dir, task_id)
                print(f"  📄 Would generate: {task_id}")
                print(f"     Phases: {len(manifest['phases'])}")
                print(f"     Points: {sum(p['points'] for p in manifest['phases'])}")
                success_count += 1
            except Exception as e:
                print(f"  ❌ Error: {task_id}: {e}")
                error_count += 1
        else:
            result = process_task(tests_dir, task_id, args.overwrite)
            if result:
                success_count += 1
            elif (tests_dir / task_id / 'manifest.json').exists():
                skip_count += 1
            else:
                error_count += 1
    
    # Summary
    print()
    print("=" * 60)
    print("📊 Summary:")
    print(f"  ✅ Generated: {success_count}")
    if skip_count > 0:
        print(f"  ⏭️  Skipped: {skip_count} (already exist)")
    if error_count > 0:
        print(f"  ❌ Errors: {error_count}")
    print("=" * 60)
    
    if args.dry_run:
        print()
        print("💡 This was a dry run. Use without --dry-run to actually generate files.")
    
    sys.exit(0 if error_count == 0 else 1)


if __name__ == '__main__':
    main()
