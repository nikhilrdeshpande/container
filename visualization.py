import pandas as pd
from jinja2 import Template

def map_to_3d_coordinates(container_data):
    def extract_coordinate(loc, index):
        try:
            parts = loc.split(':')
            return int(parts[index]) if len(parts) > index else 0
        except:
            return 0

    container_data['X'] = container_data['Location'].apply(lambda loc: extract_coordinate(loc, 0))
    container_data['Y'] = container_data['Location'].apply(lambda loc: extract_coordinate(loc, 1))
    container_data['Z'] = container_data['Location'].apply(lambda loc: extract_coordinate(loc, 2))
    return container_data

def visualize_containers_3d(container_data):
    container_data = map_to_3d_coordinates(container_data)    
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>3D Ship Visualization</title>
        <style>
            body { margin: 0; }
            canvas { display: block; }
        </style>
    </head>
    <body>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
        <script>
            console.log('Container Data:', {{container_data}});
            const containerData = {{ container_data | safe }};
            console.log('Container Data:', containerData);

            // Setup scene, camera, and renderer
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer();
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);

            // Load ship model
            const loader = new THREE.GLTFLoader();
            loader.load('/static/scene.gltf', function(gltf) {
                const ship = gltf.scene;
                scene.add(ship);
                animate();
            }, undefined, function(error) {
                console.error('An error happened during loading the GLTF model:', error);
            });

            // Add containers
            containerData.forEach(container => {
                const geometry = new THREE.BoxGeometry(container.Length, container.Height, container.Width);
                const material = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
                const cube = new THREE.Mesh(geometry, material);
                cube.position.set(container.X, container.Y, container.Z);
                scene.add(cube);
                console.log('Added container:', container);
            });

            // Setup camera position
            camera.position.z = 10;

            // Animation loop
            function animate() {
                requestAnimationFrame(animate);
                renderer.render(scene, camera);
            }

            animate();
        </script>
    </body>
    </html>
    """
    
    template = Template(html_template)
    html = template.render(container_data=container_data.to_dict(orient='records'))
    return html