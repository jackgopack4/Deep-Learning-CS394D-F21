

def train(model, log_dir=None, train_data=None, valid_data=None, optimizer=None, batch_size=128, resize=None, n_epochs=10,
          device=None, is_resnet=False):
    import torch
    import torch.utils.tensorboard as tb
    from data import load
    import numpy as np

    if train_data is None:
        train_data = load.get_dogs_and_cats(resize=resize, batch_size=batch_size, is_resnet=is_resnet)
    if valid_data is None:
        valid_data = load.get_dogs_and_cats('valid', resize=resize, batch_size=batch_size, is_resnet=is_resnet)
    if optimizer is None:
        optimizer = torch.optim.Adam(model.parameters())

    # Transfer the data to a GPU (optional)
    if device is not None:
        model = model.to(device)

    # Add a logger
    train_logger, valid_logger = None, None
    if log_dir is not None:
        train_logger = tb.SummaryWriter(log_dir+"/train", flush_secs=5)
        valid_logger = tb.SummaryWriter(log_dir+"/valid", flush_secs=5)

    # Construct the loss and accuracy functions
    loss = torch.nn.BCEWithLogitsLoss()
    accuracy = lambda o, l: ((o > 0).long() == l.long()).float()

    # Train the network
    global_step = 0
    for epoch in range(n_epochs):

        accuracies = []
        model.train()
        for it, (data, label) in enumerate(train_data):
            # Transfer the data to a GPU (optional)
            if device is not None:
                data, label = data.to(device), label.to(device)

            # Produce the output
            o = model(data)

            # Compute the loss and accuracy
            loss_val = loss(o, label.float())
            accuracies.extend(accuracy(o, label).detach().cpu().numpy())

            # log
            if train_logger is not None:
                train_logger.add_scalar('loss', loss_val, global_step=global_step)

            # Take a gradient step
            optimizer.zero_grad()
            loss_val.backward()
            optimizer.step()

            global_step += 1

        # log
        if train_logger is not None:
            train_logger.add_scalar('accuracy', np.mean(accuracies), global_step=global_step)

        val_accuracies = []
        model.eval()
        for it, (data, label) in enumerate(valid_data):
            # Transfer the data to a GPU (optional)
            if device is not None:
                data, label = data.to(device), label.to(device)
            # Produce the output
            o = model(data)
            # Compute the accuracy
            val_accuracies.extend(accuracy(o, label).detach().cpu().numpy())

        # log
        if valid_logger is not None:
            valid_logger.add_scalar('accuracy', np.mean(val_accuracies), global_step=global_step)
        else:
            print('epoch = % 3d   train accuracy = %0.3f   valid accuracy = %0.3f'%(epoch, np.mean(accuracies), np.mean(val_accuracies)))
