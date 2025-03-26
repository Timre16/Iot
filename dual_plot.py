import matplotlib.pyplot as plt
import numpy as np

def read_data(filename):
    data = np.loadtxt(filename)
    return data[:, 0], data[:, 1]

def plot_data(x1, y1, x2, y2):
    plt.figure(figsize=(15, 5))
    plt.plot(x1, y1, marker='o', linestyle='-', color='r', markersize=2, label='Simulation Air')
    plt.plot(x2, y2, marker='s', linestyle='-', color='b', markersize=2, label='Masurement Air')
    plt.xlabel('Frequency GHz')
    plt.ylabel('Amplitude dB')
    plt.title('Combined Plots')
    plt.legend()
    plt.grid(True)
    plt.show()

def main():
    filename1 = "C:/Users/timei/Desktop/Daten.txt"
    filename2 = "C:/Users/timei/Desktop/Graph.txt"
    
    x1, y1 = read_data(filename1)
    x2, y2 = read_data(filename2)
    
    plot_data(x1, y1, x2, y2)

if __name__ == "__main__":
    main()
