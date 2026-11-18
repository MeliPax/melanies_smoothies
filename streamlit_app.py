# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests  
from cryptography.hazmat.primitives import serialization

p_key = serialization.load_pem_private_key(
    st.secrets["snowflake_key"]["pem"].encode(),
    password=None,
)


pkb = p_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

try:
    cnx = st.connection("snowflake", private_key=pkb)
    session = cnx.session()
except Exception as e:
    st.error(str(e))
    st.stop()




# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# # Replace with secure connection
# cnx = st.connection("snowflake")
# session = cnx.session()
my_dataframe = session.table('smoothies.public.fruit_options').select(col('FRUIT_NAME'), col('SEARCH_ON'))
# st.dataframe(data=my_dataframe, use_container_width=True)
# st.stop()

# Convert the Snowpark Dataframe to a Pandas Dataframe so we can use the LOC function
pd_df = my_dataframe.to_pandas()
st.dataframe(pd_df)
st.stop()


ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:'
    , my_dataframe
    , max_selections=5
)


if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
    ingredients_string += fruit_chosen + ' '

    search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
    st.write('The search value for ', fruit_chosen, ' is ', search_on, '.')

    st.subheader(fruit_chosen + ' Nutrition Information')
    smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/" + search_on)
    sf_df = st.dataframe(data=smoothiefroot_response.json(), width='stretch')

    my_insert_stmt = """ insert into smoothies.public.orders(ingredients, name_on_order)
        values ('""" + ingredients_string + """','""" + name_on_order + """')"""

    #st.write(my_insert_stmt)

    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success('Your Smoothie is ordered, ' + name_on_order + '!', icon="✅")
