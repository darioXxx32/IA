import flwr as fl
from client import FlowerClient
from dataset import load_data, partition_data_iid
import torch
from torch.utils.data import DataLoader

NUM_CLIENTS = 3

# 1. Cargar y particionar datos
print("Cargando y particionando datos MNIST...")
train_dataset, test_dataset = load_data('../data')
partitions = partition_data_iid(train_dataset, NUM_CLIENTS)

# 2. Crear dataloaders
trainloaders = [DataLoader(partition, batch_size=32, shuffle=True) for partition in partitions]
testloader = DataLoader(test_dataset, batch_size=32)

def client_fn(cid: str) -> fl.client.Client:
    """Crea un cliente Flower para la simulación."""
    client_id = int(cid)
    return FlowerClient(trainloaders[client_id], testloader).to_client()

if __name__ == "__main__":
    # 3. Definir la estrategia (FedAvg por ahora)
    strategy = fl.server.strategy.FedAvg(
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_fit_clients=NUM_CLIENTS,
        min_evaluate_clients=NUM_CLIENTS,
        min_available_clients=NUM_CLIENTS,
    )

    print(f"Iniciando simulación federada con {NUM_CLIENTS} clientes...")
    
    # 4. Iniciar la simulación (Fase 0)
    fl.simulation.start_simulation(
        client_fn=client_fn,
        num_clients=NUM_CLIENTS,
        config=fl.server.ServerConfig(num_rounds=5),
        strategy=strategy,
    )
