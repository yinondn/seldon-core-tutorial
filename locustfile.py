from locust import HttpUser, task


class ModelServingUser(HttpUser):
    @task
    def iris_model_prediction(self):
        self.client.post(
            url="/seldon/my-models/iris-model/api/v1.0/predictions",
            json=dict(
                data=dict(
                    ndarray=[[1, 2, 3, 4]]
                )
            )
        )
