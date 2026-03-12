from ursina import *
from ursina.shaders import lit_with_shadows_shader 

app = Ursina()

window.color = color.azure 
sky = Sky(color=color.azure)
AmbientLight(intensity=0.5)
sun = DirectionalLight()
sun.look_at(Vec3(1, -1, 1))
cam = EditorCamera()
grid = Entity(model=Grid(20, 20), rotation_x=90, scale=20, color=color.white33)

robot = Entity(
    model='models/360_sphere_robot_no_glass.glb', 
    color=color.gray, 
    x=0, z=0,
    shader=lit_with_shadows_shader
)

robot_label = Text(
    text='Drone D-1',
    parent=robot,
    y=0.5,
    scale=5,
    origin=(0, 0),
    color=color.white
)

def update():
    # robot_label.look_at(camera)
    robot_label.rotation_x += 180

def input(key):
    if key == 'c':
        cam.enabled = not cam.enabled
        if not cam.enabled:
            camera.orthographic = True
            camera.position = (0, 5, 0)
            camera.rotation_x = 180
            robot_label.rotation_y = 90
        else:
            robot_label.rotation_y = 90
            camera.orthographic = False

app.run()