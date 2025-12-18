## Развертывание приложения

### Установка зависимостей Ansible

Перед развертыванием кластера необходимо установить требуемые Ansible коллекции. Файл `ansible/requirements.yml` содержит список необходимых коллекций (например, `vitabaks.autobase`).

Используем Python версии 3.12

Для установки зависимостей выполните:

```bash
cd ansible
ansible-galaxy collection install -r requirements.yml
```

### Развертывание PostgreSQL кластера

Для развертывания PostgreSQL кластера с HAProxy load balancing используйте:

```bash
cd ansible
ansible-playbook -i inventory.ini start_cluster.yaml -e "dcs_type=etcd with_haproxy_load_balancing=true"
```

### Остановка и очистка кластера

Для остановки и очистки развернутого кластера:

```bash
cd ansible
ansible-playbook -i inventory.ini teardown_pgcluster.yml
```

### Работа с Kubernetes

#### Настройка kubeconfig

Перед работой с Kubernetes необходимо экспортировать переменную окружения `KUBECONFIG`:

```bash
export KUBECONFIG=<path to student_2.yaml>
```

#### Управление Helm релизом

**Удаление существующего релиза (если есть):**

```bash
kubectl config set-cluster kubernetes --insecure-skip-tls-verify=true
```

```bash
helm uninstall api-chart -n sre-cource-student-2
```

**Установка Helm chart:**

```bash
helm install api-chart ./helm/api-chart -n sre-cource-student-2
```

#### Доступ к Swagger UI

Для доступа к Swagger UI с API документацией на localhost:

```bash
kubectl port-forward -n sre-cource-student-2 svc/api-chart 8080:80
```
Swagger будет доступен по адресу: `http://localhost:8080/swagger/index.html`
