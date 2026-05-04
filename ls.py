from analyzer import GitHubUserAnalyzer

def main():
    print("=========== GitHub User Analyzer ===========\n")
    
    username = input("Enter GitHub username: ")

    # Create analyzer object
    analyzer = GitHubUserAnalyzer(username)

    try:
        # Fetch user info
        analyzer.fetch_user_info()

        # Fetch repo info
        analyzer.fetch_repos()

        # Display final summary
        analyzer.display_summary()

    except Exception as e:
        print("\nError:", e)

if __name__ == "__main__":
    main()