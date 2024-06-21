import random
import json
import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import matplotlib.pyplot as plt

class SensorNetwork:
    def __init__(self, sensors, energy_levels, range_value, measuring_area, poi):
        self.sensors = np.array(sensors)
        self.energy_levels = np.array(energy_levels, dtype=np.float64)
        self.range_value = range_value
        self.measuring_area = measuring_area
        self.poi = np.array([p for p in poi if self.is_within_bounds(p)])  # Ensure POI are within bounds
        self.coverage_grid = np.zeros(measuring_area)
        self.active_sensors = np.ones(len(sensors), dtype=bool)
        self.battery_history = []
        self.activity_history = []

    @classmethod
    def from_file(cls, file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
            num_sensors = data["num_sensors"]
            range_value = data["range_value"]
            measuring_area = data["measuring_area"]
            num_poi = data["num_poi"]

            sensors = [[random.randint(0, measuring_area[0]), random.randint(0, measuring_area[1])] for _ in range(num_sensors)]
            energy_levels = [100] * num_sensors
            poi = [[random.randint(0, measuring_area[0]), random.randint(0, measuring_area[1])] for _ in range(num_poi)]

        return cls(sensors, energy_levels, range_value, measuring_area, poi)

    def is_within_bounds(self, point):
        x, y = point
        return 0 <= x < self.measuring_area[0] and 0 <= y < self.measuring_area[1]

    def update_battery_levels(self):
        self.energy_levels[self.active_sensors] -= np.random.uniform(0, 0.1, size=self.energy_levels[self.active_sensors].shape)
        self.energy_levels = np.clip(self.energy_levels, 0, 100)
        self.battery_history.append(self.energy_levels.copy())
        self.activity_history.append(self.active_sensors.copy())
        self.deactivate_sensors()

    def deactivate_sensors(self):
        # First, turn off all sensors
        self.active_sensors[:] = False

        # Then, activate only the necessary sensors to cover all POIs
        for poi in self.poi:
            for idx, sensor in enumerate(self.sensors):
                if self.energy_levels[idx] > 0 and not self.active_sensors[idx]:
                    if np.linalg.norm(sensor - poi) <= self.range_value:
                        self.active_sensors[idx] = True
                        break  # Only need one sensor to cover this POI

        self.update_coverage_grid()

    def update_coverage_grid(self):
        self.coverage_grid = np.zeros(self.measuring_area)
        for idx, s in enumerate(self.sensors):
            if not self.active_sensors[idx]:
                continue
            x, y = s
            for dx in range(int(-self.range_value), int(self.range_value + 1)):
                for dy in range(int(-self.range_value), int(self.range_value + 1)):
                    if 0 <= x + dx < self.measuring_area[0] and 0 <= y + dy < self.measuring_area[1]:
                        if dx ** 2 + dy ** 2 <= self.range_value ** 2:
                            self.coverage_grid[x + dx, y + dy] = 1

    def coverage_percentage(self):
        self.update_coverage_grid()
        covered_poi = sum(1 for x, y in self.poi if self.coverage_grid[x, y] == 1)
        total_poi = len(self.poi)
        return (covered_poi / total_poi) * 100

    def plot_network(self, title):
        plt.figure()
        plt.scatter(self.sensors[:, 0], self.sensors[:, 1], c='red', label='Sensors')
        plt.scatter(self.poi[:, 0], self.poi[:, 1], c='blue', label='POI')
        
        # Add circles to represent sensor range
        for sensor in self.sensors:
            circle = plt.Circle((sensor[0], sensor[1]), self.range_value, color='gray', alpha=0.3)
            plt.gca().add_patch(circle)
        
        plt.legend()
        plt.xlabel('X Coordinate')
        plt.ylabel('Y Coordinate')
        plt.title(title)
        plt.show()

    def plot_coverage_over_time(self, coverage_data):
        plt.figure()
        plt.plot(coverage_data)
        plt.xlabel('Time Steps')
        plt.ylabel('Coverage Percentage')
        plt.title('Coverage Percentage Over Time')
        plt.show()

    def plot_battery_levels_over_time(self):
        plt.figure()
        battery_history = np.array(self.battery_history)
        for i in range(battery_history.shape[1]):
            plt.plot(battery_history[:, i], label=f'Sensor {i}')
        plt.xlabel('Time Steps')
        plt.ylabel('Battery Level')
        plt.title('Battery Levels Over Time')
        plt.legend()
        plt.show()

    def plot_activity_over_time(self):
        plt.figure()
        activity_history = np.array(self.activity_history)
        active_sensors_count = np.sum(activity_history, axis=1)
        plt.plot(active_sensors_count, label='Active Sensors')
        plt.xlabel('Time Steps')
        plt.ylabel('Number of Active Sensors')
        plt.title('Sensor Activity Over Time')
        plt.legend()
        plt.show()

class SimulatedAnnealing:
    def __init__(self, initial_solution, temperature, cooling_rate, iteration_limit, sensor_network):
        self.initial_temperature = temperature
        self.temperature = temperature
        self.cooling_rate = cooling_rate
        self.iteration_limit = iteration_limit
        self.current_solution = initial_solution
        self.sensor_network = sensor_network
        self.current_score = self.evaluate(self.current_solution)
        self.coverage_history = []

    def evaluate(self, solution):
        self.sensor_network.sensors = np.array(solution)
        return self.sensor_network.coverage_percentage()

    def neighbor(self, solution):
        new_solution = solution.copy()
        idx = random.randint(0, len(solution) - 1)
        new_solution[idx] = [random.randint(0, self.sensor_network.measuring_area[0] - 1),
                             random.randint(0, self.sensor_network.measuring_area[1] - 1)]
        return new_solution

    def optimize(self):
        for _ in range(self.iteration_limit):
            new_solution = self.neighbor(self.current_solution)
            new_score = self.evaluate(new_solution)
            if new_score > self.current_score:
                self.current_solution = new_solution
                self.current_score = new_score
            elif random.random() < np.exp((new_score - self.current_score) / self.temperature):
                self.current_solution = new_solution
                self.current_score = new_score
            self.temperature *= self.cooling_rate
            self.coverage_history.append(self.current_score)
            self.sensor_network.update_battery_levels()
        return self.current_solution, self.current_score

    def plot_coverage_history(self):
        plt.figure()
        plt.plot(self.coverage_history)
        plt.xlabel('Iterations')
        plt.ylabel('Coverage Percentage')
        plt.title('Coverage Percentage Over Iterations')
        plt.show()

def load_configuration():
    file_path = filedialog.askopenfilename()
    return file_path

def main():
    root = tk.Tk()
    root.title("Sensor Network Simulation")

    def configure_manual():
        manual_window = tk.Toplevel(root)
        manual_window.title("Manual Configuration")

        tk.Label(manual_window, text="Number of Sensors:").grid(row=0, column=0)
        tk.Label(manual_window, text="Sensor Range:").grid(row=1, column=0)
        tk.Label(manual_window, text="Measuring Area (x, y):").grid(row=2, column=0)
        tk.Label(manual_window, text="Number of POI:").grid(row=3, column=0)

        num_sensors_entry = tk.Entry(manual_window)
        range_entry = tk.Entry(manual_window)
        area_x_entry = tk.Entry(manual_window)
        area_y_entry = tk.Entry(manual_window)
        num_poi_entry = tk.Entry(manual_window)

        num_sensors_entry.grid(row=0, column=1)
        range_entry.grid(row=1, column=1)
        area_x_entry.grid(row=2, column=1)
        area_y_entry.grid(row=2, column=2)
        num_poi_entry.grid(row=3, column=1)

        def set_manual_config():
            num_sensors = int(num_sensors_entry.get())
            range_value = float(range_entry.get())
            measuring_area = [int(area_x_entry.get()), int(area_y_entry.get())]
            num_poi = int(num_poi_entry.get())

            sensors = [[random.randint(0, measuring_area[0]), random.randint(0, measuring_area[1])] for _ in range(num_sensors)]
            energy_levels = [100] * num_sensors
            poi = [[random.randint(0, measuring_area[0]), random.randint(0, measuring_area[1])] for _ in range(num_poi)]

            global sensor_network
            sensor_network = SensorNetwork(sensors, energy_levels, range_value, measuring_area, poi)
            manual_window.destroy()

        tk.Button(manual_window, text="Set Configuration", command=set_manual_config).grid(row=4, column=0, columnspan=3)

    def configure_file():
        file_path = load_configuration()
        global sensor_network
        sensor_network = SensorNetwork.from_file(file_path)

    tk.Button(root, text="Load Configuration from File", command=configure_file).grid(row=0, column=0)
    tk.Button(root, text="Manual Configuration", command=configure_manual).grid(row=0, column=1)

    tk.Label(root, text="Initial Temperature:").grid(row=1, column=0)
    tk.Label(root, text="Cooling Rate:").grid(row=2, column=0)
    tk.Label(root, text="Iteration Limit:").grid(row=3, column=0)

    initial_temp_entry = tk.Entry(root)
    cooling_rate_entry = tk.Entry(root)
    iteration_limit_entry = tk.Entry(root)

    initial_temp_entry.grid(row=1, column=1)
    cooling_rate_entry.grid(row=2, column=1)
    iteration_limit_entry.grid(row=3, column=1)

    initial_temp_entry.insert(0, "1000")
    cooling_rate_entry.insert(0, "0.95")
    iteration_limit_entry.insert(0, "1000")

    def run_simulation():
        try:
            temperature = float(initial_temp_entry.get())
            cooling_rate = float(cooling_rate_entry.get())
            iteration_limit = int(iteration_limit_entry.get())

            initial_solution = sensor_network.sensors.tolist()

            sensor_network.plot_network('Sensor Network Coverage before optimization')

            sa = SimulatedAnnealing(initial_solution, temperature, cooling_rate, iteration_limit, sensor_network)
            print("OPTIMIZING")
            final_solution, final_score = sa.optimize()
            
            sensor_network.plot_network('Sensor Network Coverage after optimization')
            sa.plot_coverage_history()
            sensor_network.plot_battery_levels_over_time()
            sensor_network.plot_activity_over_time()

             # Analyze simulation results
            analyze_simulation_results(sa.coverage_history, sensor_network.battery_history, sensor_network.activity_history)

            messagebox.showinfo("Simulation Complete", f"Final Coverage: {final_score:.2f}%")
        except ValueError as e:
            messagebox.showerror("Input Error", "Please enter valid input values.")
        except NameError as e:
            messagebox.showerror("Configuration Error", "Please configure the sensor network first.")

    run_button = tk.Button(root, text="Run Simulation", command=run_simulation)
    run_button.grid(row=4, column=0, columnspan=2)

    root.mainloop()

    # Statistical analysis
def analyze_simulation_results(coverage_history, battery_history, activity_history):
    # Convert history lists to numpy arrays for easier manipulation
    coverage_history = np.array(coverage_history)
    battery_history = np.array(battery_history)
    activity_history = np.array(activity_history)
    
    # Coverage Percentage Analysis
    avg_coverage = np.mean(coverage_history)
    avg_battery_levels = np.mean(battery_history, axis=0)
    min_battery_levels = np.min(battery_history, axis=0)
    max_battery_levels = np.max(battery_history, axis=0)
    print("STATISTICAL ANALYSIS")
    print(f'Average Coverage Percentage Over Time (Avg: {avg_coverage:.2f}%)')
    print("Average Battery Levels:", avg_battery_levels)
    print("Minimum Battery Levels:", min_battery_levels)
    print("Maximum Battery Levels:", max_battery_levels)

    # Sensor Activity Analysis
    active_sensors_count = np.sum(activity_history, axis=1)
    avg_active_sensors = np.mean(active_sensors_count)
    print("Average Number of Active Sensors:", avg_active_sensors)





if __name__ == "__main__":
    main()
