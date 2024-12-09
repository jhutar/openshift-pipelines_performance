import urllib3
from random import shuffle
from urllib3.exceptions import InsecureRequestWarning
from locust import HttpUser, task

urllib3.disable_warnings(InsecureRequestWarning)


class FetchResultLogTest(HttpUser):
    '''
    Fetch Log content for specific PipelineRun or TaskRun
    '''
    def on_start(self):
        self.client.verify = False

        # Fetch all records and extract one id
        records = self.client.get(
            "/apis/results.tekton.dev/v1alpha2/parents/-/results/-/records",
            name='fetch_id').json()['records']

        self.log_ids = []
        self.log_ids_index = 0

        # Look for TaskRun object to fetch logs
        for record in records:
            if "data" in record and 'type' in record['data'] and (
                record['data']['type'].endswith(".TaskRun")
                # Uncomment below to include PipelineRun for search
                # or record['data']['type'].endswith(".PipelineRun")
            ):
                self.log_ids.append(record['name'].replace("/records", "/logs"))
                break

        # Small Randomness in picking first taskrun for fetching log
        shuffle(self.log_ids)

    def validate_response(self, response):
        '''Check whether the log response contains actual data when returning 200 status code'''
        if response.status_code == 200 and len(response.text) > 0:
            return True
        return False

    @task
    def get_log(self) -> None:
        """Get Log content for a result"""
        ###if self.log_ids:   # or is this "if ..." really needed? I would expect Locust only start launching tasks once on_start finishes executing
            self.log_ids_index += 1
            if self.log_ids_index == len(self.log_ids):
                self.log_ids_index = 0
    
            with self.client.get(
                f"/apis/results.tekton.dev/v1alpha2/parents/{self.log_ids[self.log_ids_index]}",
                name="/log",
                catch_response=True
            ) as response:
                if self.validate_response(response):
                    response.success()
                else:
                    response.failure("Response validation failed")
