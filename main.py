from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
import json

app = FastAPI()

class patient_update(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0)]
    gender: Annotated[Optional[Literal['male', 'female', 'other']], Field(default=None)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]

class Patient(BaseModel):
    id: Annotated[str, Field(..., description='Enter Patient ID')]
    name: Annotated[str, Field(..., max_length=50, examples=['Meet Joshi'])]
    city: Annotated[str, Field(..., description='Enter Your city here')]
    age: Annotated[int, Field(..., gt=0, description='Enter Your age here')]
    gender: Annotated[Literal['male', 'female', 'others'], Field(..., description='Gender')]
    weight: Annotated[float, Field(..., description='Enter Weight in kg')]
    height: Annotated[float, Field(..., description='Enter your height in m')]

    # @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight / (self.height**2),2)
        return bmi
    
    @computed_field
    @property
    def calculate_verdict(self) -> str:
        if self.bmi < 18.5:
            return 'underweight'
        elif self.bmi < 30:
            return 'normal'
        else:
            return 'obese'

def data_load():
    with open('patients.json', 'r') as f:
        data = json.load(f)
    return data

def save_data(data):
    with open('patients.json', 'w') as f:
        json.dump(data,f)

@app.get("/")
def hello():
    return {'message' : 'Patient Management API'}

@app.get("/about")
def about():
    return {'message' : 'A fully functinal API to manage your Patient record'}

@app.get('/view')
def view():
    data = data_load()
    return data

@app.get('/patient/{patient_id}')
def view_patient(patient_id : str = Path(..., description="Patient_id from DB", examples="P001")):
    data = data_load()
    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404, detail='Patient not found')
    # return {'ERROR' : 'This patient is not registered'}

@app.get('/sort')
def sort_by(sort_by : str = Query(..., description='sort on the basis of height, weight, bmi'), order : str = Query('asc', description='sort on the basis of ASC and DESC')):
    valid_fields = ['weight', 'height', 'bmi']

    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f'please sort from the {valid_fields}')
    
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail='please select from ASC or DESC')
    
    data = data_load()

    sort_order = True if order=='desc' else False

    sorted_order = sorted(data.values(), key = lambda x : x.get(sort_by, 0), reverse=sort_order)

    return sorted_order

@app.post('/create')
def create_new_patient(patient: Patient):
    #first load the data
    data = data_load()
    #check if patient exists
    if patient.id in data:
        raise HTTPException(status_code=400, detail='Patient ID already exists try another ID')
    
    #now adding new data
    data[patient.id] = patient.model_dump(exclude=['id'])

    save_data(data)

    return JSONResponse(status_code=201, content={'message': 'Patient created successfully'})

@app.put('/update/{patient_id}')
def update_details(patient_id: str, patient_update: patient_update):
    data = data_load()

    if patient_id not in data:
        raise HTTPException(status_code=400, detail='Patient doesnt Exist')
    
    existing_data = data[patient_id]

    new_details = patient_update.model_dump(exclude_unset=True)

    for key, value in new_details.items():
        existing_data[key] = value

    # existing_data -> pydantic_object -> updated bmi + verdict -> pydantic_object -> dict
    existing_data['id'] = patient_id
    patient_pydantic_object = Patient(**existing_data)
    existing_data = patient_pydantic_object.model_dump(exclude=['id'])

    data[patient_id] = existing_data

    save_data(data)

    return JSONResponse(status_code=200, content={'message' : 'patient updated'})

@app.delete('/delete/{patient_id}')
def delete_patient(patient_id : str):

    data = data_load()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient ID does not exist')
    
    del data[patient_id]

    save_data(data)

    return JSONResponse(status_code=200, content={'message' : 'Successfully deleted'})