from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

expected_utm_param_values = {
    'utm_source': 'braze',
    'utm_medium': 'email',
    'utm_campaign': 'take-a-peek-october-2024',
    'utm_content': '',
    'utm_term': '',
}

def check_image_attributes(image_tag):

    src = image_tag.get('src', '')

    
    print(f"🏞️  Image")
    text_full_report = f"🏞️  Image\n"

    if src.startswith("https://braze-images.com"):
        text_full_report += f"💚 Link src formatted properly\n"
    else:
        print(f"❌ Incorrect link src: {src} \nmissing correct pre-fix braze-images.com/")
        text_full_report += f"❌ Incorrect link src: {src} \nmissing correct pre-fix braze-images.com/\n"

    
    border_value = image_tag.get('border')
    if border_value!='0':
        print(f"❌ Incorrect border value: {border_value}")
        text_full_report += f"❌ Incorrect border value: {border_value}\n"
    else:
        text_full_report += f"💚 Correct image border value: 0\n"

    return text_full_report + "\n"

# pass in braze api for the html

def check_query_params(href):

    parsed_url = urlparse(href)
    query_params = parse_qs(parsed_url.query)    
    
    text_full_report = f"🔗 Link {href}\n"

    error = False
    for key, value in expected_utm_param_values.items():
        if key not in query_params:
            print(f"❌ Missing utm parameter: {key}")
            text_full_report += f"❌ Missing utm parameter: {key}\n"
            error=True
        elif key in ['utm_content', 'utm_term']:
            if not query_params[key][0]:
                print(f"❌ {key} is empty")
                text_full_report += f"❌ {key} is empty\n"
            else:
                text_full_report += f"💡 {key}: {query_params[key][0]}\n"
                print(f"💡 {key}: {query_params[key][0]}")

        elif query_params[key][0] != value:
            print(f" ❌ {key} value is incorrect. Expected '{value}', but got '{value}'") 
            text_full_report += f" ❌ {key} value is incorrect. Expected '{value}', but got '{value}'\n"
            error=True
        
    if not error:
        print(f"All other expected parameters are correct")   
        text_full_report += f"All other expected parameters are correct\n"
    
    return text_full_report + "\n"

def check_frag_id(href,anchor_tags_with_name):

    if href[1:] in anchor_tags_with_name:
        return f"🔎 Fragment Identifier:\n💚 {href[1:]} ref found in file\n\n"
    else:
        print(f"🔎 Fragment Identifier:\n❌{href[1:]} ref not found in file")
        return f"🔎 Fragment Identifier:\n❌ {href[1:]} ref not found in file\n\n"
    
def check_html_file(file_path):
    
    full_report=""
    with open(file_path, 'r', encoding='utf-8') as file:
        
        soup = BeautifulSoup(file, 'html.parser')
        
        anchor_img_tags = soup.find_all(['a','img'])
        anchor_tags_with_name = [tag.attrs['name'] for tag in anchor_img_tags if 'name' in tag.attrs]
        
        
        for tag in anchor_img_tags[:3]:
            full_report += f"Line number: {tag.sourceline}\n"

            if tag.name=='a':
                if 'href' in tag.attrs.keys():
                    href = tag['href']
                if href.startswith('#'):
                    full_report += check_frag_id(href=href,anchor_tags_with_name=anchor_tags_with_name)
                else:
                    full_report += check_query_params(href=href)

            else:
                # check for link start
                full_report += check_image_attributes(image_tag=tag) 

        #     print("\n\n")
    
    return full_report

        
           
            
if __name__ == '__main__':
    html_file_path = 'index.html'  # Replace with the actual path
    
    full_report = check_html_file(html_file_path)

    with open('output_test_2.txt', 'w') as file:
        file.write(full_report)

