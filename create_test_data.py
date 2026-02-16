"""
Generate test point clouds for Phase 2 testing
Creates reference and target clouds with simulated terrain changes
"""
import numpy as np
import open3d as o3d


def create_terrain_cloud(filename: str, num_points: int = 10000, seed: int = 42,
                         add_deformation: bool = False):
    """Create a terrain-like point cloud with optional deformation"""
    np.random.seed(seed)
    
    # Generate points in a grid-like pattern
    side = int(np.sqrt(num_points))
    x = np.linspace(0, 20, side)
    y = np.linspace(0, 20, side)
    xx, yy = np.meshgrid(x, y)
    
    # Create terrain with hills and valleys
    zz = (2 * np.sin(xx * 0.5) * np.cos(yy * 0.5) + 
          1.5 * np.sin(xx * 0.3) * np.sin(yy * 0.4) +
          5)  # Base elevation
    
    # Add deformation for target cloud (simulated erosion/deposition)
    if add_deformation:
        # Erosion zone (negative change)
        erosion_mask = (xx > 8) & (xx < 12) & (yy > 8) & (yy < 12)
        zz[erosion_mask] -= 0.5  # 0.5m erosion
        
        # Deposition zone (positive change)
        deposition_mask = (xx > 14) & (xx < 18) & (yy > 5) & (yy < 9)
        zz[deposition_mask] += 0.4  # 0.4m deposition
        
        # Small random changes everywhere
        zz += np.random.randn(*zz.shape) * 0.05
    else:
        # Just add noise to reference
        zz += np.random.randn(*zz.shape) * 0.03
    
    # Flatten to point cloud
    points = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])
    
    # Add some random points (vegetation, noise)
    num_random = num_points - len(points)
    if num_random > 0:
        random_points = np.random.rand(num_random, 3) * [20, 20, 3] + [0, 0, 5]
        points = np.vstack([points, random_points])
    
    # Create point cloud
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    
    # Add colors based on height
    z_values = points[:, 2]
    z_min, z_max = z_values.min(), z_values.max()
    z_normalized = (z_values - z_min) / (z_max - z_min)
    
    # Terrain-like colors (green to brown to white)
    colors = np.zeros((len(points), 3))
    colors[:, 1] = 0.6 * (1 - z_normalized) + 0.2  # Green channel
    colors[:, 0] = 0.4 * z_normalized + 0.3  # Red channel
    colors[:, 2] = 0.2 * z_normalized + 0.1  # Blue channel
    
    pcd.colors = o3d.utility.Vector3dVector(colors)
    
    # Estimate normals (needed for ICP and signed distance)
    pcd.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.5, max_nn=30)
    )
    
    # Save
    o3d.io.write_point_cloud(filename, pcd)
    print(f"Created {filename} with {len(points):,} points")
    return pcd


if __name__ == '__main__':
    print("Generating Phase 2 test data...")
    print("=" * 50)
    
    # Create reference cloud (baseline terrain)
    print("\n1. Creating reference terrain...")
    ref = create_terrain_cloud('test_reference.ply', num_points=10000, seed=42, 
                               add_deformation=False)
    
    # Create target cloud (with changes)
    print("\n2. Creating target terrain (with changes)...")
    target = create_terrain_cloud('test_target.ply', num_points=10000, seed=42,
                                  add_deformation=True)
    
    # Add slight misalignment to target (for ICP testing)
    print("\n3. Adding misalignment to target...")
    transformation = np.eye(4)
    transformation[0, 3] = 0.3  # 0.3m shift in X
    transformation[1, 3] = -0.2  # 0.2m shift in Y
    transformation[2, 3] = 0.1  # 0.1m shift in Z
    # Small rotation
    angle = np.radians(5)  # 5 degree rotation
    transformation[0, 0] = np.cos(angle)
    transformation[0, 1] = -np.sin(angle)
    transformation[1, 0] = np.sin(angle)
    transformation[1, 1] = np.cos(angle)
    
    target.transform(transformation)
    o3d.io.write_point_cloud('test_target.ply', target)
    
    print("\n" + "=" * 50)
    print("✓ Test data created successfully!")
    print("\nFiles created:")
    print("  - test_reference.ply (baseline terrain)")
    print("  - test_target.ply (with erosion, deposition, and misalignment)")
    print("\nExpected analysis results:")
    print("  - ICP should align target to reference")
    print("  - Ground removal should detect horizontal plane")
    print("  - Change map should show:")
    print("    • Erosion zone (blue): ~0.5m loss")
    print("    • Deposition zone (red): ~0.4m gain")
    print("    • Noise elsewhere: ~0.05m variation")
